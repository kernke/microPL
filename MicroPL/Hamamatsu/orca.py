from pylablib.devices import DCAM

from PyQt5.QtWidgets import QHBoxLayout,QVBoxLayout, QLineEdit, QWidget,QLabel,QGridLayout,QPushButton
from PyQt5.QtCore import  QObject, pyqtSignal, pyqtSlot,QRunnable,QTimer


import pyqtgraph as pg
import numpy as np
import datetime

class CameraSignalspatial(QObject):
    camsignal = pyqtSignal(object)   

class CameraHandler_spatial(QRunnable):
    def __init__(self, device):
        super().__init__()
        self.device = device
        self.signals = CameraSignalspatial()
    
    @pyqtSlot()
    def run(self): # A slot takes no params
        cimg=self.device.acquire(self.device.acqtime_spatial)
        print("max intens: "+str(np.max(cimg)))
        self.signals.camsignal.emit(cimg)



class Orca():
    def __init__(self,app):
        self.app=app
        try:
            self.cam = DCAM.DCAMCamera(idx=0)
            self.cam.setup_acquisition(mode="snap")
            print("orca connected")
            self.app.add_log("Orca connected")
            self.connected=True
        except:
            self.connected=False
            print("orca dummy mode")
            self.app.add_log("Orca dummy mode")

        self.acqtime_spatial=0.2
        self.binning=1
        self.crosshair=False
        self.live_mode_running=False
        self.live_mode_latency=300
        self.maximized=False
        

    def acquire(self,exposure_time):
        self.cam.set_exposure(exposure_time)
        self.cam.start_acquisition()
        self.cam.wait_for_frame()
        image = self.cam.read_newest_image()
        self.cam.stop_acquisition()
        return image

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
        self.expanded=False
        self.app.heading_label(layoutright,"Spatial Camera",self.expand)

        self.dropdown=QVBoxLayout()

        layoutacqtime_spatial=QHBoxLayout()
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(self.app.standard_width)
        widget.setText(str(self.acqtime_spatial))
        layoutacqtime_spatial.addWidget(widget)
        widget.textEdited.connect(self.acqtime_spatial_edited)

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
        
        layoutmax=QHBoxLayout()
        self.maxbtn=self.app.normal_button(layoutmax,"Maximize View",self.maximize)
        self.maxbtn.setFixedWidth(110)
        layoutmax.addStretch()
        self.resbtn=self.app.normal_button(layoutmax,"Resolution (2048)",self.set_resolution)
        self.resbtn.setFixedWidth(110)


        self.dropdown.addLayout(layoutmax)

        layoutright.addLayout(self.dropdown)

        self.app.set_layout_visible(self.dropdown,False)

        layoutright.addItem(self.app.vspace)


    def set_resolution(self):
        self.window = self.app.buttonmask3(self.app,["2048x2048","1024x1024","512x512"],"resolution")#device,roi
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
        layout= QGridLayout()
        self.cw.setLayout(layout)
        layout.setSpacing(0)
        view = pg.GraphicsView()
        view.setBackground(None)
        vb = pg.ViewBox()
        vb.setAspectLocked()
        #view.setFixedSize(512,512)
        view.setCentralItem(vb)

        layout.addWidget(view, 0, 0)#,4, 0)

        self.img=pg.ImageItem()
        self.img_data=cimg
        self.img.setImage(cimg)
        vb.addItem(self.img)
        vb.invertY(True)
        vb.autoRange()
        
        hist = pg.HistogramLUTWidget()#gradientPosition="left")
        #hist.move(-100,100)
        hist.setLevelMode(mode="mono")
        hist.setBackground(None)
        hist.gradient.loadPreset("plasma")
        #hist.gradient.setColorMap(pg.colormap.get('plasma')) 
        layout.addWidget(hist, 0, 1)
        hist.setImageItem(self.img)
        
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

    def acquire_clicked_spatial(self):
        self.app.metadata_spatial["mode"]="spatial"
        self.app.metadata_spatial["time_stamp"]=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        self.app.metadata_spatial["acquisition_time"]=self.acqtime_spatial
        xacq,yacq=self.app.stage.xpos,self.app.stage.ypos
        self.app.metadata_spatial["stage_x"]=xacq
        self.app.metadata_spatial["stage_y"]=yacq
        self.app.metadata_spatial["unsaved"]=True
        if not self.live_mode_running:
            self.app.add_log("spatial img acquired")
        self.camera_handler =CameraHandler_spatial(self) 
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
                if np.double(s)>10:
                    self.acqtime_spatial=10.
                else:
                    self.acqtime_spatial=np.double(s)
                    if self.live_mode_running and self.acqtime_spatial>0.001: #
                        self.timer.stop()
                        self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))

    def live_mode(self):
        if not self.live_mode_running:
            self.app.add_log("spatial camera Live mode started")
            self.timer=QTimer()
            self.timer.timeout.connect(self.acquire_clicked_spatial)
            self.live_mode_running=True
            self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))
            self.btnlive.setText("stop")
            self.btnlive.setStyleSheet("background-color: green;color: black")
        else:
            self.app.add_log("spatial camera Live mode stopped")
            self.live_mode_running=False
            self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
