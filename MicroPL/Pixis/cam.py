import pylablib as pll
from pylablib.devices import PrincetonInstruments
import pyqtgraph as pg
import numpy as np
import time
from PyQt5.QtCore import  QObject, pyqtSignal, pyqtSlot,QRunnable,QTimer

from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QWidget,QLabel,QGridLayout,QCheckBox,QVBoxLayout

import datetime

class CameraSignalspectral(QObject):

    camsignal = pyqtSignal(object)   

class CameraHandler_spectral(QRunnable):

    def __init__(self, device):
        super().__init__()

        self.device = device
        self.signals = CameraSignalspectral()

    
    @pyqtSlot()
    def run(self): # A slot takes no params
        cimg=self.device.acquire(self.device.acqtime_spectral,0, 1024, 0, 256, 1,1,show=False)
        print("max intens: "+str(np.max(cimg)))
        self.signals.camsignal.emit(cimg)


class Pixis():
    def __init__(self,app):
        self.app=app
        try:
            pll.par["devices/dlls/picam"] = r"C:\Program Files\Common Files\Princeton Instruments\Picam\Runtime"
            cameras = PrincetonInstruments.list_cameras()
            print('Camera found:', cameras)

            self.cam = PrincetonInstruments.PicamCamera('09166914')
            self.cam.setup_acquisition(mode='snap') # mode= [snap, sequence], [nframes = X]

            self.connected=True
            self.app.add_log("Pixis connected")

        except:
            self.connected=False
            print("pixis dummy mode")
            self.app.add_log("Pixis dummy mode")

        
        self.acqtime_spectral=0.2
        self.live_mode_latency=300
        self.save_full_image=True
        self.live_mode_running=False
        self.maximized=False
        #pprint.pp(dir(cam))

        #def pixelfmt():
        #self.pix_format = cam.get_attribute_value("Pixel Format")  # get the current pixel format


    
    def acquire(self, t, x0,x1,y0,y1, hbin,vbin,show=True):
        self.cam.set_exposure(t)
        #attr = self.cam.get_exposure()
        #pprint.pp("Exposure time: " + str(attr))
        
        #check for potential comment
        self.cam.set_roi(x0, x1, y0, y1, hbin, vbin)

        self.cam.start_acquisition()
        self.cam.wait_for_frame()
        img = self.cam.read_newest_image()
        self.cam.stop_acquisition()
        
        return img
        
    def chip_temp(self):
        temp = self.cam.get_attribute_value("Sensor Temperature Reading")
        self.app.add_log("Sensor Temperature: " + str(temp))
        temp_status = self.cam.get_attribute_value("Sensor Temperature Status")
        self.app.add_log("Temperature status: " + str(temp_status))




    def close(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()
        
        self.cam.set_attribute_value("Shutter Timing Mode", 'Normal')
        self.cam.close()

        print("Camera disconnected")
        


    def spectral_camera_show(self,layoutv):
        #self.layoutv=QVBoxLayout()
        cimg=np.ones([256,1024],dtype=np.uint16)
        cimg[:,:5]=65535
        cimg[:,-5:]=65535
        cimg[:5,:]=65535
        cimg[-5:,:]=65535


        # image view window start########################################################
        self.cw = QWidget() 
        layout = QGridLayout()
        self.cw.setLayout(layout)
        layout.setSpacing(0)
        view = pg.GraphicsView()
        #view.setFixedSize(512,128)
        view.setBackground(None)
        vb = pg.ViewBox()
        #vb.setAspectLocked()
        view.setCentralItem(vb)
        
        layout.addWidget(view, 0, 0)

        self.img=pg.ImageItem()
        self.img_data=cimg.T[:,::-1]
        self.img.setImage(cimg.T[:,::-1])
        vb.addItem(self.img)
        vb.invertY(True)
        vb.autoRange()
        
        hist = pg.HistogramLUTWidget()#gradientPosition="left")#,orientation="horizontal")

        hist.setBackground(None)
        hist.setLevelMode(mode="mono")
        hist.gradient.loadPreset("greyclip")
        layout.addWidget(hist, 0, 1)
        hist.setImageItem(self.img)

        # ROI
        #max_bounds = pg.QtCore.QRectF(0, 0, 1024, 256)
        self.roi=pg.RectROI([0, 100], [1024, 20], pen=(0,9))#,maxBounds=max_bounds)

        vb.addItem(self.roi)
        
        # image view window end########################################################
        layoutv.addWidget(self.cw,1)    
        # 1D spectrum view start ###################################################
        self.roiplot = pg.PlotWidget()
        self.roiplot.setBackground(None)
        self.roiplot.setLabel('bottom', 'Wavelength', units='nm')
        self.roiplot.setLabel('left', 'Intensity ( 0 - 65535 )', units='')
        self.roiplot.getAxis("left").enableAutoSIPrefix(True)

        #roiplot.setFixedHeight(350)
        self.roi.sigRegionChanged.connect(self.updateRoi)
        data = self.roi.getArrayRegion(self.img.image, img=self.img)
        
        yvalues=data.mean(axis=-1)
        self.roi.curve=self.roiplot.plot(self.app.monochromator.spectrum_x_axis,yvalues )        
        # 1D spectrum view end  ###################################################
        
        layoutv.addWidget(self.roiplot,2)
        #layoutleft.addLayout(self.layoutv,3)

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)

    def spectral_camera_ui(self,layoutright):   
        self.expanded=False 
        self.app.heading_label(layoutright,"Spectral Camera",self.expand)

        self.dropdown=QVBoxLayout()
       
        self.checkbox = QCheckBox('save full chip image', self.app)
        self.checkbox.setStyleSheet("color:white")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.checkbox_full_saving)
        self.dropdown.addWidget(self.checkbox)

        layoutacqtime_spectral=QHBoxLayout()
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(self.app.standard_width)
        widget.setText(str(self.acqtime_spectral))
        layoutacqtime_spectral.addWidget(widget)
        widget.textEdited.connect(self.acqtime_spectral_edited)

        label = QLabel("acquisition time (s)")
        label.setStyleSheet("color:white")
        layoutacqtime_spectral.addWidget(label)

        self.btnsave_spectral =self.app.normal_button(layoutacqtime_spectral,"Save",self.app.h5saving.save_to_h5_spectral)
        

        self.dropdown.addLayout(layoutacqtime_spectral)

        layoutacqbutton=QHBoxLayout()
        self.btnacq_spectral = self.app.normal_button(layoutacqbutton,"Acquire",self.acquire_clicked_spectral)
        layoutacqbutton.addStretch()

        self.app.normal_button(layoutacqbutton,"set ROI",self.entry_window_roi)

        layoutacqbutton.addStretch()

        self.btnlive = self.app.normal_button(layoutacqbutton,"Live",self.live_mode)
        self.timer=QTimer()
        self.timer.timeout.connect(self.acquire_clicked_spectral)


        self.dropdown.addLayout(layoutacqbutton)

        layoutauto=QHBoxLayout()
        self.autobtn=self.app.normal_button(layoutauto,"Auto Exposure",self.auto_exposure)
        self.autobtn.setFixedWidth(110)
        layoutauto.addStretch()
        self.shutterbtn=self.app.normal_button(layoutauto,"Shutter (Normal)",self.shutter_setting)
        self.shutterbtn.setFixedWidth(120)

        self.dropdown.addLayout(layoutauto)

        layoutright.addLayout(self.dropdown)


        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()
        self.ctempbtn=self.app.normal_button(layoutmax,"Chip Temp. (Logging)",self.chip_temp)
        self.ctempbtn.setFixedWidth(120)

        self.dropdown.addLayout(layoutmax)

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        
        layoutright.addItem(self.app.vspace)

    def auto_exposure(self):
        pass


    def shutter_setting(self):
        self.window = self.app.buttonmask3(self.app,["Normal","Open","Closed"],"shutter")#device,roi
        heading_string="Set the mechanical shutter of the spectrometer/camera. "
        heading_string+="(Normal: opens and closes the shutter on acquisition)"
        self.window.setHeading(heading_string)
        self.window.location_on_the_screen()
        self.window.show()

    def maximize(self):
        if self.maximized:
            self.maximized=False
            self.app.orca.cw.setHidden(False)
            self.app.midleft.setHidden(False)
            self.maxbtn.setText("Maximize View")
        else:
            self.maximized=True
            self.app.orca.cw.setHidden(True)
            self.app.midleft.setHidden(True)
            self.maxbtn.setText("Minimize View")

    def live_mode(self):
        if not self.live_mode_running:
            self.live_mode_running=True
            self.timer.start(int(self.acqtime_spectral*1000+self.live_mode_latency))
            self.btnlive.setText("stop")
            self.shutterbtn.setText("Shutter (Open)")
            self.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
            self.btnlive.setStyleSheet("background-color: green;color: black")
            self.app.add_log("Spectral camera shutter opened permanently")
            self.app.add_log("spectral camera Live mode started")
        else:

            self.live_mode_running=False
            self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
            self.shutterbtn.setText("Shutter (Normal)")
 
            self.cam.set_attribute_value("Shutter Timing Mode", 'Normal')
            self.app.add_log("Spectral camera shutter returned to 'normal'")
            self.app.add_log("spectral camera Live mode stopped")

    def checkbox_full_saving(self,state):
        if state == 2:
            print("Full image saving enabled")
            self.save_full_image=True
        else:
            self.save_full_image=False
            print("Full image saving disabled")


    def acqtime_spectral_edited(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                if np.double(s)>10:
                    self.acqtime_spectral=10.
                else:
                    self.acqtime_spectral=np.double(s)
                    if self.live_mode_running and self.acqtime_spectral>0.001:
                        self.timer.stop()
                        self.timer.start(int(self.acqtime_spectral*1000+self.live_mode_latency))



    def updateRoi(self):
        if self.roi is None:
            return
        data = self.roi.getArrayRegion(self.img.image, img=self.img)
        spectrum_y_axis=data.mean(axis=-1)
        start=next((i for i, x in enumerate(spectrum_y_axis) if x), None) 
        
        rect=self.roi.getState()
        end=int(np.round(rect["size"][0]))-next((i for i, x in enumerate(spectrum_y_axis[::-1]) if x), None)
        
        if start is None:
            start=0
            end=1024
        self.app.monochromator.spectrum_x_axis=self.app.monochromator.grating_wavelength(self.roi)
        
        x_axis_plot=self.app.monochromator.spectrum_x_axis[start:end]
        self.roi.curve.setData(x_axis_plot,spectrum_y_axis[start:end] )
        self.wavelength_min=x_axis_plot[0]
        self.wavelength_max=x_axis_plot[-1]

        self.max_at_wavelength=self.app.monochromator.spectrum_x_axis[np.argmax(spectrum_y_axis)]
        
    def entry_window_roi(self):
        self.w = self.app.entrymask4(True,self.app)
        self.w.setHeading("ROI in Pixels with chip dimension 1024x256\nY increases from top to bottom\n(entries must be integers)")
        self.w.location_on_the_screen()
        self.w.show()  

    def acquire_clicked_spectral(self):
        self.app.metadata_spectral["mode"]="spectral"
        self.app.metadata_spectral["ROI_origin"]=(self.roi.pos()[0],self.roi.pos()[1])
        self.app.metadata_spectral["ROI_extent"]=(self.roi.size()[0],self.roi.size()[1])
        self.app.metadata_spectral["time_stamp"]=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        self.app.metadata_spectral["acquisition_time"]=self.acqtime_spectral
        self.app.metadata_spectral["center_wavelength"]=self.app.monochromator.wavelength
        xacq,yacq=self.app.stage.xpos,self.app.stage.ypos
        self.app.metadata_spectral["stage_x"]=xacq
        self.app.metadata_spectral["stage_y"]=yacq
        self.app.metadata_spectral["grating"]=self.app.monochromator.grating_actual
        self.app.metadata_spectral["unsaved"]=True
        if not self.live_mode_running:
            self.app.add_log("spectral img acquired")
        self.camera_handler =CameraHandler_spectral(self) 
        self.camera_handler.signals.camsignal.connect(self.image_from_thread_spectral)
        self.app.threadpool.start(self.camera_handler)



    def image_from_thread_spectral(self,cimg):
        self.img.setImage(cimg.T[::-1])
        self.img_data=cimg.T[::-1]
        imgmax=np.max(cimg)
        statustext="Spectral Max: "+str(int(imgmax))+"\n"
        
        self.updateRoi()

        statustext+="ROI Max at: "+str(np.round(self.max_at_wavelength,2))
        self.app.status_pixis.setText(statustext+" nm")
        statustext2="from: "+str(np.round(self.wavelength_min,2))+" nm\nto: "+str(np.round(self.wavelength_max,2))+" nm"
        self.app.status_mono.setText(statustext2)
        if self.app.h5saving.save_on_acquire_bool:
            self.app.h5saving.save_to_h5_spectral()


