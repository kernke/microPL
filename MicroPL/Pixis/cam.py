import pylablib as pll
from pylablib.devices import PrincetonInstruments
import pyqtgraph as pg
import pprint
import numpy as np
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


#shutter_timing = cam.get_attribute_value("Shutter Timing Mode")
#pprint.pp("Shutter timing: " + str(shutter_timing))
#attr = cam._list_attributes()
#pprint.pp(attr)
#cam.setup_shutter("open")

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
            self.app.add_log("pixis connected")
        except:
            self.connected=False
            print("pixis dummy mode")
            self.app.add_log("pixis dummy mode")

        
        self.acqtime_spectral=1
        self.live_mode_latency=300
        self.save_full_image=True
        self.live_mode_running=False
        #pprint.pp(dir(cam))

        #def pixelfmt():
        #self.pix_format = cam.get_attribute_value("Pixel Format")  # get the current pixel format


    
    def acquire(self, t, x0,x1,y0,y1, hbin,vbin,show=True):
        self.cam.set_exposure(t)
        attr = self.cam.get_exposure()
        #pprint.pp("Exposure time: " + str(attr))
        self.cam.set_roi(x0, x1, y0, y1, hbin, vbin)

        self.cam.start_acquisition()
        self.cam.wait_for_frame()
        img = self.cam.read_newest_image()
        self.cam.stop_acquisition()
        
        
        #pprint.pp(np.shape(img))
        #if show:
        #    pg.image(img)
        return img
        
    def chip_temp(self):
        temp = self.cam.get_attribute_value("Sensor Temperature Reading")
        pprint.pp("Sensor Temperature: " + str(temp))
        temp_status = self.cam.get_attribute_value("Sensor Temperature Status")
        pprint.pp("Temperature status: " + str(temp_status))




    def close(self):
        self.cam.close()
        print("Camera disconnected")
        


    def spectral_camera_show(self,layoutleft):

        cimg=np.zeros([256,1024],dtype=np.uint16)
        cimg[:,:5]=65535
        cimg[:,-5:]=65535
        cimg[:5,:]=65535
        cimg[-5:,:]=65535


        # image view window start########################################################
        cw = QWidget() 
        layout = QGridLayout()
        cw.setLayout(layout)
        layout.setSpacing(0)
        view = pg.GraphicsView()
        #view.setFixedSize(512,128)
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
        
        hist = pg.HistogramLUTWidget(gradientPosition="left")#,orientation="horizontal")
        hist.setLevelMode(mode="mono")
        layout.addWidget(hist, 0, 1)
        hist.setImageItem(self.img)

        # ROI
        self.roi=pg.RectROI([0, 100], [1024, 20], pen=(0,9))
        vb.addItem(self.roi)
        
        # image view window end########################################################
        layoutleft.addWidget(cw,1)    
        # 1D spectrum view start ###################################################
        roiplot = pg.PlotWidget()

        roiplot.setLabel('bottom', 'Wavelength', units='nm')
        roiplot.setLabel('left', 'Intensity ( 0 - 65535 )', units='')
        roiplot.getAxis("left").enableAutoSIPrefix(True)

        #roiplot.setFixedHeight(350)
        self.roi.sigRegionChanged.connect(self.updateRoi)
        data = self.roi.getArrayRegion(self.img.image, img=self.img)
        
        yvalues=data.mean(axis=-1)
        self.roi.curve=roiplot.plot(self.app.monochromator.spectrum_x_axis,yvalues )        
        # 1D spectrum view end  ###################################################
        layoutleft.addWidget(roiplot,2)

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

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        
        label = QLabel(" ")
        layoutright.addWidget(label)
        label = QLabel(" ")
        layoutright.addWidget(label)



    def live_mode(self):
        if not self.live_mode_running:
            #self.timer=QTimer()
            #self.timer.timeout.connect(self.acquire_clicked_spectral)
            self.live_mode_running=True
            if self.app.orca.live_mode_running and False:
                self.app.orca.timer.stop()
                other_timer=self.app.orca.acqtime_spatial*1000+self.app.orca.live_mode_latency
                timer_time=int(other_timer+self.live_mode_latency+700)
                self.app.orca.timer.start(timer_time)

                this_timer=self.acqtime_spectral*1000+self.live_mode_latency
                timer_time=int(this_timer+self.app.orca.live_mode_latency+700)
                self.timer.start(timer_time)
            else:
                self.timer.start(int(self.acqtime_spectral*1000+self.live_mode_latency))#200
            self.btnlive.setText("stop")
            self.btnlive.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running=False
            self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")

    def checkbox_full_saving(self,state):
        if state == 2:
            print("Full image saving enabled")
            self.save_full_image=True
        else:
            self.save_full_image=False
            print("Full image saving disabled")


    def acqtime_spectral_edited(self,s):
        if s:
            self.acqtime_spectral=np.double(s)
            if self.live_mode_running and self.acqtime_spectral>0.0001:
                if self.app.orca.live_mode_running and False:
                    latency=self.live_mode_latency+self.app.orca.live_mode_latency+700
                else:
                    latency=self.live_mode_latency
                self.timer.stop()
                self.timer.start(int(self.acqtime_spectral*1000+latency))#+200



    def updateRoi(self):
        if self.roi is None:
            return
        data = self.roi.getArrayRegion(self.img.image, img=self.img)
        self.app.monochromator.spectrum_x_axis=self.app.monochromator.grating_wavelength(self.roi)
        self.roi.curve.setData(self.app.monochromator.spectrum_x_axis, data.mean(axis=-1))

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
        xacq,yacq=self.app.stage.get_position()
        self.app.metadata_spectral["stage_x"]=xacq
        self.app.metadata_spectral["stage_y"]=yacq
        self.app.metadata_spectral["grating"]=self.app.monochromator.grating_actual
        self.app.metadata_spectral["unsaved"]=True
        self.camera_handler =CameraHandler_spectral(self) 
        self.camera_handler.signals.camsignal.connect(self.image_from_thread_spectral)
        self.app.threadpool.start(self.camera_handler)



    def image_from_thread_spectral(self,cimg):
        self.img.setImage(cimg.T[::-1])
        self.img_data=cimg.T[::-1]
        self.updateRoi()
        if self.app.h5saving.save_on_acquire_bool:
            self.app.h5saving.save_to_h5_spectral()


