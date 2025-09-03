from pylablib.devices import DCAM

from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout, QLineEdit, QWidget,QLabel,QGridLayout,QPushButton
from PyQt5.QtCore import  QObject, pyqtSignal, pyqtSlot,QRunnable,QTimer

import time
import pyqtgraph as pg
import numpy as np
import datetime

class CameraSignalspatial(QObject):
    camsignal = pyqtSignal(object)
    #complete_signal=pyqtSignal(bool)

class CameraHandler_spatial(QRunnable):
    def __init__(self, device,event=None):
        super().__init__()
        self.orca = device
        self.signals = CameraSignalspatial()
        self.event=event
    
    @pyqtSlot()
    def run(self): 

        acq_s=self.orca.acqtime_spatial
        #print(self.orca.auto_expose_start)
        if self.orca.auto_exposure_activated:
            self.orca.cam.set_exposure(self.orca.auto_expose_start)
            self.orca.cam.start_acquisition()
            self.orca.cam.wait_for_frame()
            img = self.orca.cam.read_newest_image()
            self.orca.cam.stop_acquisition()

            img_max=np.max(img).astype(np.double)
            counts_per_s= img_max/self.orca.auto_expose_start

            acq_s=np.round(65535./counts_per_s,2)
            if acq_s>self.orca.auto_expose_max:
                acq_s=self.orca.auto_expose_max
            elif acq_s<self.orca.auto_expose_min:
                acq_s=self.orca.auto_expose_min

            self.orca.cam.set_exposure(acq_s)

        #else:

        if acq_s>10:
            number_of_full=int(acq_s//10)
            remaining=acq_s-number_of_full*10
            if remaining>0.01:
                self.orca.cam.set_exposure(remaining)
                self.orca.cam.start_acquisition()
                self.orca.cam.wait_for_frame()
                img = self.orca.cam.read_newest_image()
                self.orca.cam.stop_acquisition()
            else:
                self.orca.cam.set_exposure(10)
                self.orca.cam.start_acquisition()
                self.orca.cam.wait_for_frame()
                img = self.orca.cam.read_newest_image()
                self.orca.cam.stop_acquisition()
                number_of_full -= 1

            self.orca.cam.set_exposure(10)
            for i in range(number_of_full):
                self.orca.cam.start_acquisition()
                self.orca.cam.wait_for_frame()
                img += self.orca.cam.read_newest_image()
                self.orca.cam.stop_acquisition()


        else:
            self.orca.cam.start_acquisition()
            self.orca.cam.wait_for_frame()
            img = self.orca.cam.read_newest_image()
            self.orca.cam.stop_acquisition()

        #this line is a bit unclean, as it indirectly returns the acqtime
        self.orca.acqtime_spatial=acq_s

        self.signals.camsignal.emit(img)
        #self.signals.complete_signal.emit(True)
        if self.event:
            self.event.set()





        #self.orca.cam.start_acquisition()
        #self.orca.cam.wait_for_frame()
        #image = self.orca.cam.read_newest_image()
        #self.orca.cam.stop_acquisition()
        # A slot takes no params
        #cimg=self.device.acquire(self.device.acqtime_spatial)
        #print("max intens: "+str(np.max(cimg)))
        #self.signals.camsignal.emit(image)



class Orca():
    def __init__(self,app):
        self.app=app
        self.acqtime_spatial=0.2
        try:
            self.cam = DCAM.DCAMCamera(idx=0)
            self.cam.setup_acquisition(mode="snap")
            print("orca connected")
            self.app.add_log("Orca connected")
            self.connected=True
            self.cam.set_exposure(self.acqtime_spatial)
        except:
            self.connected=False
            print("orca dummy mode")
            self.app.add_log("Orca dummy mode")

        self.acqtime_spatial=0.2
        self.binning=1
        self.crosshair=False
        self.live_mode_running=False
        self.live_mode_just_stopped=False
        self.live_mode_latency=300
        self.maximized=False

        self.auto_exposure_activated=False
        self.auto_expose_start=0.1
        self.auto_expose_min=0.01
        self.auto_expose_max=10      

        self.counter=0  

    def disconnect(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()

        self.cam.close()
        print("orca disconnected")

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)


    def spatial_camera_ui(self,layoutright):
        self.timer=QTimer()
        self.timer.timeout.connect(self.acquire_clicked_spatial)

        self.expanded=False
        self.app.heading_label(layoutright,"Spatial Camera",self.expand)

        self.dropdown=QVBoxLayout()

        layoutacqtime_spatial=QHBoxLayout()
        self.acqwidget = QLineEdit()
        self.acqwidget.setStyleSheet("background-color: lightGray")
        self.acqwidget.setMaxLength(7)
        self.acqwidget.setFixedWidth(self.app.standard_width)
        self.acqwidget.setText(str(self.acqtime_spatial))
        layoutacqtime_spatial.addWidget(self.acqwidget)
        self.acqwidget.textEdited.connect(self.acqtime_spatial_edited)

        label = QLabel("acquisition time (s)")
        label.setStyleSheet("color:white")
        layoutacqtime_spatial.addWidget(label)
        self.btnsave_spatial =self.app.normal_button(layoutacqtime_spatial,"Save",self.app.h5saving.save_to_h5_spatial)

        self.dropdown.addLayout(layoutacqtime_spatial)


        layoutacqbutton=QHBoxLayout()
        self.btnacq_spatial = self.app.normal_button(layoutacqbutton,"Acquire",self.acquire_clicked_spatial)
        layoutacqbutton.addStretch()
        self.app.normal_button(layoutacqbutton,"Crosshair",self.overlay_crosshair)
        layoutacqbutton.addStretch()

        
        self.btnlive = self.app.normal_button(layoutacqbutton,"Live",self.live_mode)


        self.dropdown.addLayout(layoutacqbutton)
        
        layoutauto=QHBoxLayout()
        self.autobtn=self.app.normal_button(layoutauto,"Auto Exposure",self.auto_exposure)
        self.autobtn.setFixedWidth(110)
        layoutauto.addStretch()
        self.resbtn=self.app.normal_button(layoutauto,"Resolution (2048)",self.set_resolution)
        self.resbtn.setFixedWidth(110)


        self.dropdown.addLayout(layoutauto)

        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()
        layoutright.addLayout(self.dropdown)
        self.dropdown.addLayout(layoutmax)

        self.app.set_layout_visible(self.dropdown,False)

        layoutright.addItem(self.app.vspace)

    def auto_exposure(self):
        if self.auto_exposure_activated:
            self.auto_exposure_activated=False
            self.autobtn.setStyleSheet("background-color:lightgrey")
            if self.live_mode_running:
                self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))
        else:
            labellist=["Start (s)","Min (s)","Max (s)"]
            defaultlist=[self.auto_expose_start,self.auto_expose_min,self.auto_expose_max]
            heading_string="Turn on AutoExposure with the following settings: "
            heading_string+="Start refers to the time of the first test acquisition and Min and Max limit the range of exposure times. "
            heading_string+="Any Exposure above 10 seconds consists of a Multiframe sum, with the longest exposure time being 10 s."
            self.window = self.app.entrymask3(self.app,"auto_spatial",defaultlist,labellist,heading_string)
            self.window.location_on_the_screen()
            self.window.show()



    def set_resolution(self):
        self.window = self.app.buttonmask3(self.app,["2048x2048","1024x1024","512x512"],"resolution")
        self.window.setHeading("Set the resolution of the saved image from the Orca spatial camera")
        self.window.location_on_the_screen()
        self.window.show()

    def spatial_camera_show(self,layoutleft):

        cimg=np.ones([2048,2048],dtype=np.uint16)
        cimg[:,:5]=65535
        cimg[:,-5:]=65535
        cimg[:5,:]=65535
        cimg[-5:,:]=65535
        
        # image view window start########################################################
        self.cw = QWidget() 
        #self.label_up = QLabel("Title", self.cw)
        #self.label_up.move(100, -10)
        #self.label_up.setStyleSheet("color: white;font-size: 13pt")
        layout= QHBoxLayout()#QGridLayout()
        self.cw.setLayout(layout)
        view = pg.GraphicsView()
        view.setBackground(None)
        vb = pg.ViewBox()
        vb.setAspectLocked()
        view.setCentralItem(vb)

        layout.addWidget(view,10)

        self.img=pg.ImageItem()
        self.img_data=cimg
        self.img.setImage(cimg)
        vb.addItem(self.img)
        vb.invertY(True)
        vb.autoRange()
        
        hist = pg.HistogramLUTWidget(gradientPosition="left")
        hist.setLevelMode(mode="mono")
        hist.setBackground(None)
        hist.gradient.loadPreset("plasma")
        #hist.gradient.setColorMap(pg.colormap.get('plasma')) 
        layout.addWidget(hist,3)#, 0, 1)
        hist.setImageItem(self.img)

        #histogram = hist.getHistogramItem()#getPlotItem()#.histItem#histogram#getHistogramLUTItem()#getHistogramWidget()
        #axis=histogram.get_axis("left")
        #axis.setLabel('Intensity ( 0 - 65535 )', units='')


        # image view window end########################################################
        layoutleft.addWidget(self.cw,3)    


    def maximize(self):
        if self.maximized:
            self.maximized=False
            self.app.pixis.cw.setHidden(False)
            self.app.pixis.roiplot.setHidden(False)
            self.app.midleft.setHidden(False)
            self.maxbtn.setText("Maximize View")
        else:
            self.maximized=True
            self.app.pixis.cw.setHidden(True)
            self.app.pixis.roiplot.setHidden(True)
            self.app.midleft.setHidden(True)
            self.maxbtn.setText("Minimize View")


    def overlay_crosshair(self):
        if self.crosshair:
            self.crosshair=False
            self.img.setImage(self.img_data)
        else:
            self.crosshair=True
            crosshaired_img=np.copy(self.img_data)
            crosshaired_img[1021:1027,:]=np.max(self.img_data)
            crosshaired_img[:,1021:1027]=np.max(self.img_data)
            self.img.setImage(crosshaired_img)


    def image_from_thread_spatial(self,cimg):
        if self.binning==1:
            self.img_data=cimg.T[:,::-1]
        elif self.binning==2:
            self.img_data=np.reshape(cimg.T[:,::-1],(1024,2,1024,2)).mean(-1).mean(1)
        else:
            self.img_data=np.reshape(cimg.T[:,::-1],(512,4,512,4)).mean(-1).mean(1)

        imgmax=np.max(cimg)
        imgmean=np.mean(cimg)

        self.app.metadata_spatial["acquisition_time"]=self.acqtime_spatial
        if not self.live_mode_running:
            if self.live_mode_just_stopped:
                self.live_mode_just_stopped=False
            else:
                self.app.update_log("spatial img "+str(self.counter)+ " acquired")
                self.counter+=1
            if self.auto_exposure_activated:
                self.app.add_log("auto exposure (s):"+str(self.acqtime_spatial))
        self.acqwidget.setText(str(self.acqtime_spatial))

        if imgmax>65534:
            self.app.update_log("Warning: spatial img oversaturation")

        self.app.status_orca.setText("Spatial Max: "+str(int(imgmax))+"\n"+"Spatial Mean: "+str(int(imgmean)))
        if self.crosshair:
            crosshaired_img=np.copy(self.img_data)
            if self.binning==1:
                crosshaired_img[1021:1027,:]=imgmax
                crosshaired_img[:,1021:1027]=imgmax
            elif self.binning==2:
                crosshaired_img[510:514,:]=imgmax
                crosshaired_img[:,510:514]=imgmax
            else:
                crosshaired_img[255:257,:]=imgmax
                crosshaired_img[:,255:257]=imgmax
            self.img.setImage(crosshaired_img)

        else: 
            self.img.setImage(self.img_data)
        if self.app.h5saving.save_on_acquire_bool:
            self.app.h5saving.save_to_h5_spatial()

        if self.live_mode_running and self.auto_exposure_activated:
            self.acquire_clicked_spatial()

    def acquire_clicked_spatial(self,event=None):
        self.app.metadata_spatial["mode"]="spatial"
        self.app.metadata_spatial["time_stamp"]=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        xacq,yacq=self.app.stage.xpos,self.app.stage.ypos
        self.app.metadata_spatial["stage_x_mm"]=xacq
        self.app.metadata_spatial["stage_y_mm"]=yacq
        self.app.metadata_spatial["unsaved"]=True
        if self.app.keysight.output_on:
            self.app.metadata_spatial["current_A"]=self.app.keysight.currentA_actual
            self.app.metadata_spatial["voltage_V"]=self.app.keysight.voltage_actual
        if not self.live_mode_running:
            self.app.add_log("spatial img Acq. started")
        self.camera_handler =CameraHandler_spatial(self,event) 
        self.camera_handler.signals.camsignal.connect(self.image_from_thread_spatial)
        self.app.threadpool.start(self.camera_handler)

    def acqtime_spatial_edited(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                if np.double(s)>10 and self.live_mode_running:
                    self.acqtime_spatial=10.
                    self.app.add_log("in Live mode max: 10 s")
                else:
                    self.acqtime_spatial=np.double(s)

                if self.acqtime_spatial>0.001:
                    if self.live_mode_running: 
                        self.timer.stop()
                        self.cam.set_exposure(self.acqtime_spatial)
                        self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))
                    else:
                        self.cam.set_exposure(self.acqtime_spatial)
                        
    def live_mode(self):
        if not self.live_mode_running:
            self.app.add_log("spatial camera Live mode started")
            self.live_mode_running=True
            self.btnlive.setText("stop")
            self.btnlive.setStyleSheet("background-color: green;color: black")
            if self.auto_exposure_activated:
                self.acquire_clicked_spatial()
            else:
                self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))

        else:
            self.app.add_log("spatial camera Live mode stopped")
            self.live_mode_running=False
            self.live_mode_just_stopped=True
            if not self.auto_exposure_activated:
                self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
