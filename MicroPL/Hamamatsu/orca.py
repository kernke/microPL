from pylablib.devices import DCAM

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QWidget,QLabel,QGridLayout,QComboBox,QApplication,QCheckBox
from PyQt5.QtCore import  QObject, pyqtSignal, pyqtSlot,QRunnable,QTimer


import pyqtgraph as pg

import numpy as np
import datetime
#from .Application.utility import *


class CameraSignalspatial(QObject):
    camsignal = pyqtSignal(object)   

class CameraHandler_spatial(QRunnable):
    def __init__(self, device):
        super().__init__()
        self.device = device
        self.signals = CameraSignalspatial()
    
    @pyqtSlot()
    def run(self): # A slot takes no params
        cimg_s=self.device.acquire(self.device.acqtime_spatial)
        print("max intens: "+str(np.max(cimg_s)))
        self.signals.camsignal.emit(cimg_s)



class Orca():
    def __init__(self,app):

        self.cam = DCAM.DCAMCamera(idx=0)
        self.cam.setup_acquisition(mode="snap")
        print("orca connected")

        self.connected=True

        self.app=app
        self.acqtime_spatial=1
        self.crosshair=False
        self.live_mode_running_s=False
        self.live_mode_latency_s=400
        

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

            
            self.btnlive_s = self.app.normal_button(layoutacqbutton,"Live",self.live_mode_s)

            layoutright.addLayout(layoutacqbutton)
            layoutright.addStretch()

    def spatial_camera_show(self,layoutleft):

        cimg_s=np.zeros([2048,2048],dtype=np.uint16)
        cimg_s[:,:5]=65535
        cimg_s[:,-5:]=65535
        cimg_s[:5,:]=65535
        cimg_s[-5:,:]=65535
        
        # image view window start########################################################
        cw_s = QWidget() 
        layout_s= QGridLayout()
        cw_s.setLayout(layout_s)
        layout_s.setSpacing(0)
        view_s = pg.GraphicsView()
        vb_s = pg.ViewBox()
        vb_s.setAspectLocked()
        view_s.setFixedSize(512,512)
        view_s.setCentralItem(vb_s)

        layout_s.addWidget(view_s, 0, 0)#,4, 0)

        self.img_s=pg.ImageItem()
        self.img_s_data=cimg_s
        self.img_s.setImage(cimg_s)
        vb_s.addItem(self.img_s)
        vb_s.invertY(True)
        vb_s.autoRange()
        
        hist_s = pg.HistogramLUTWidget(gradientPosition="left")
        hist_s.setLevelMode(mode="mono")
        hist_s.gradient.loadPreset("plasma")
        #hist_s.gradient.setColorMap(pg.colormap.get('plasma')) 
        layout_s.addWidget(hist_s, 0, 1)
        hist_s.setImageItem(self.img_s)
        
        # image view window end########################################################
        layoutleft.addWidget(cw_s)    



    def overlay_crosshair(self):
        if self.crosshair:
            self.crosshair=False
            self.img_s.setImage(self.img_s_data)
        else:
            self.crosshair=True
            crosshaired_img=np.copy(self.img_s_data)
            crosshaired_img[1021:1027,:]=np.max(self.img_s_data)
            crosshaired_img[:,1021:1027]=np.max(self.img_s_data)
            self.img_s.setImage(crosshaired_img)


    def image_from_thread_spatial(self,cimg):
        self.img_s_data=cimg
        if self.crosshair:
            crosshaired_img=np.copy(cimg)
            crosshaired_img[1021:1027,:]=np.max(cimg)
            crosshaired_img[:,1021:1027]=np.max(cimg)
            self.img_s.setImage(crosshaired_img)

        else: 
            self.img_s.setImage(cimg)
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
            if self.live_mode_running_s and self.acqtime_spatial>0.001: #
                if self.app.pixis.live_mode_running:
                    latency=self.app.pixis.live_mode_latency+self.live_mode_latency_s+700
                else:
                    latency=self.live_mode_latency_s
                self.timer_s.stop()
                self.timer_s.start(int(self.acqtime_spatial*1000+latency))

    def live_mode_s(self):
        if not self.live_mode_running_s:
            self.timer_s=QTimer()
            self.timer_s.timeout.connect(self.acquire_clicked_spatial)
            self.live_mode_running_s=True
            if self.app.pixis.live_mode_running:
                self.app.pixis.timer.stop()
                other_timer=self.app.pixis.acqtime_spectral*1000+self.app.pixis.live_mode_latency
                timer_time=int(other_timer+self.live_mode_latency_s+700)
                self.app.pixis.timer.start(timer_time)

                this_timer=self.acqtime_spatial*1000+self.live_mode_latency_s
                timer_time_s=int(this_timer+self.app.pixis.live_mode_latency+700)
                self.timer_s.start(timer_time_s)
            else:
                self.timer_s.start(int(self.acqtime_spatial*1000+self.live_mode_latency_s))
            self.btnlive_s.setText("stop")
            self.btnlive_s.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running_s=False
            self.timer_s.stop()
            self.btnlive_s.setText("Live")
            self.btnlive_s.setStyleSheet("background-color: lightGray;color: black")
