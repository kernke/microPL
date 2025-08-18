from pylablib.devices import DCAM

from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QWidget,QLabel,QGridLayout
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

        self.cam = DCAM.DCAMCamera(idx=0)
        self.cam.setup_acquisition(mode="snap")
        print("orca connected")

        self.connected=True

        self.app=app
        self.acqtime_spatial=1
        self.crosshair=False
        self.live_mode_running=False
        self.live_mode_latency=400
        

    def acquire(self,exposure_time):
        self.cam.set_exposure(exposure_time)
        self.cam.start_acquisition()
        self.cam.wait_for_frame()
        image = self.cam.read_newest_image()
        self.cam.stop_acquisition()
        return image

    def disconnect(self):
        self.cam.close()
        print("orca disconnected")



    def spatial_camera_ui(self,layoutright):
            self.app.heading_label(layoutright,"Spatial Camera")######################################################

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



            layoutright.addLayout(layoutacqtime_spatial)

            layoutacqbutton=QHBoxLayout()
            self.btnacq_spatial = self.app.normal_button(layoutacqbutton,"Acquire",self.acquire_clicked_spatial)
            layoutacqbutton.addStretch()
            self.app.normal_button(layoutacqbutton,"Crosshair",self.overlay_crosshair)
            layoutacqbutton.addStretch()

            
            self.btnlive = self.app.normal_button(layoutacqbutton,"Live",self.live_mode_s)

            layoutright.addLayout(layoutacqbutton)
            layoutright.addStretch()

    def spatial_camera_show(self,layoutleft):

        cimg=np.zeros([2048,2048],dtype=np.uint16)
        cimg[:,:5]=65535
        cimg[:,-5:]=65535
        cimg[:5,:]=65535
        cimg[-5:,:]=65535
        
        # image view window start########################################################
        cw = QWidget() 
        layout= QGridLayout()
        cw.setLayout(layout)
        layout.setSpacing(0)
        view = pg.GraphicsView()
        vb = pg.ViewBox()
        vb.setAspectLocked()
        view.setFixedSize(512,512)
        view.setCentralItem(vb)

        layout.addWidget(view, 0, 0)#,4, 0)

        self.img=pg.ImageItem()
        self.img_data=cimg
        self.img.setImage(cimg)
        vb.addItem(self.img)
        vb.invertY(True)
        vb.autoRange()
        
        hist = pg.HistogramLUTWidget(gradientPosition="left")
        hist.setLevelMode(mode="mono")
        hist.gradient.loadPreset("plasma")
        #hist.gradient.setColorMap(pg.colormap.get('plasma')) 
        layout.addWidget(hist, 0, 1)
        hist.setImageItem(self.img)
        
        # image view window end########################################################
        layoutleft.addWidget(cw)    



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
        self.img_data=cimg
        if self.crosshair:
            crosshaired_img=np.copy(cimg)
            crosshaired_img[1021:1027,:]=np.max(cimg)
            crosshaired_img[:,1021:1027]=np.max(cimg)
            self.img.setImage(crosshaired_img)

        else: 
            self.img.setImage(cimg)
        if self.app.h5saving.save_on_acquire_bool:
            self.app.h5saving.save_to_h5_spatial()

    def acquire_clicked_spatial(self):
        self.app.metadata_spatial["mode"]="spatial"
        self.app.metadata_spatial["time_stamp"]=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        self.app.metadata_spatial["acquisition_time"]=self.acqtime_spatial
        xacq,yacq=self.app.stage.get_position()
        self.app.metadata_spatial["stage_x"]=xacq
        self.app.metadata_spatial["stage_y"]=yacq
        self.app.metadata_spatial["unsaved"]=True
        self.camera_handler =CameraHandler_spatial(self) 
        self.camera_handler.signals.camsignal.connect(self.image_from_thread_spatial)
        self.app.threadpool.start(self.camera_handler)

    def acqtime_spatial_edited(self,s):
        if s:
            self.acqtime_spatial=np.double(s)
            if self.live_mode_running and self.acqtime_spatial>0.001: #
                if self.app.pixis.live_mode_running:
                    latency=self.app.pixis.live_mode_latency+self.live_mode_latency+700
                else:
                    latency=self.live_mode_latency
                self.timer.stop()
                self.timer.start(int(self.acqtime_spatial*1000+latency))

    def live_mode(self):
        if not self.live_mode_running:
            self.timer=QTimer()
            self.timer.timeout.connect(self.acquire_clicked_spatial)
            self.live_mode_running=True
            if self.app.pixis.live_mode_running:
                self.app.pixis.timer.stop()
                other_timer=self.app.pixis.acqtime_spectral*1000+self.app.pixis.live_mode_latency
                timer_time=int(other_timer+self.live_mode_latency+700)
                self.app.pixis.timer.start(timer_time)

                this_timer=self.acqtime_spatial*1000+self.live_mode_latency
                timer_time=int(this_timer+self.app.pixis.live_mode_latency+700)
                self.timer.start(timer_time)
            else:
                self.timer.start(int(self.acqtime_spatial*1000+self.live_mode_latency))
            self.btnlive.setText("stop")
            self.btnlive.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running=False
            self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
