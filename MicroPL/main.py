# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThreadPool#,QChecked,QTimer,
#QSize,QThread, QObject, pyqtSignal, pyqtSlot ,QRunnable
#from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget,QFileDialog,QLabel,QGridLayout,QComboBox,QApplication,QCheckBox
#,QDesktopWidget,QDialog

from .Application.gui_utility import *
from .Application.saving import Saving
from .Application.scripting import Scripting
from .Pixis.cam import Pixis
from .stage_scripts.stage import Stage
from .SCT320_Wrapper.mono import SCT320
from .Hamamatsu.orca import Orca

#color_text_on_dark="white"
#color_text_on_bright="black"
#color_interactive_stuff="lightGray"
#color_background="black"
          
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        #global roi,roiplot,device,h5saving,metadata_spatial,metadata_spectral
        self.setWindowTitle("MicroPL App")
        self.setStyleSheet("background-color: black;")#black 
        self.move(400,32)
               
        self.standard_width=55
        self.normal_button=normal_button

        self.warnwindow=WarnWindow
        self.entrymask4=EntryMask4
        self.entrymask6=EntryMask6

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
 
        
        self.h5saving=Saving(self)
        self.scripting=Scripting(self)

        self.stage = Stage(self)
        self.monochromator=SCT320(self)
        self.pixis = Pixis(self)
        self.orca = Orca(self)

        
        self.metadata_spatial=dict()
        self.metadata_spatial["unsaved"]=True

        self.metadata_spectral=dict()
        self.metadata_spectral["unsaved"]=True
        
        layoutmain = QHBoxLayout() # whole window
        layoutright = QVBoxLayout() # right side containing image,colorbar and 1D-roi-plot
        layoutleft = QVBoxLayout() # left side containing all the buttons

        # graphics show
        self.orca.spatial_camera_show(layoutleft)
        #image and colorbar

        self.pixis.spectral_camera_show(layoutleft)
        #image, colorbar and 1D-profile plot
        
        layoutmain.addLayout( layoutleft )

        # user interface buttons 
        ui= QWidget() 
        ui.setFixedWidth(300)
        ui.setLayout(layoutright)

        self.orca.spatial_camera_ui(layoutright)

        self.pixis.spectral_camera_ui(layoutright)
        
        self.monochromator.mono_ui(layoutright)

        self.stage.stage_ui(layoutright)



        self.heading_label(layoutright,"LED Power Supply")####################################################

        layoutlim=QHBoxLayout()
        label = QLabel("Set        ")
        label.setStyleSheet("color:white")
        layoutlim.addWidget(label)

        layoutlim.addStretch()
        normal_button(layoutlim,"<- Switch ->",self.power_switch)        
        #btn.setFixedWidth(80)
        layoutlim.addStretch()

        label = QLabel("Limit (max)")
        label.setStyleSheet("color:white")
        layoutlim.addWidget(label)

        layoutright.addLayout(layoutlim)

        layoutset=QHBoxLayout()
        voltwidget = QLineEdit()
        voltwidget.setStyleSheet("background-color: lightGray")
        voltwidget.setMaxLength(7)
        voltwidget.setFixedWidth(self.standard_width)
        voltwidget.setText(str(0.0))
        label = QLabel("Voltage (V)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(voltwidget)
        layoutset.addWidget(label)
        layoutset.addStretch()
        currentwidget = QLineEdit()
        currentwidget.setStyleSheet("background-color: lightGray")
        currentwidget.setMaxLength(7)
        currentwidget.setFixedWidth(self.standard_width)
        currentwidget.setText(str(0.0))
        label = QLabel("Current (mA)")
        label.setStyleSheet("color:white")
        layoutset.addWidget(label)
        layoutset.addWidget(currentwidget)
        
        layoutright.addLayout(layoutset)
        layoutright.addStretch()


        self.scripting.script_ui(layoutright)

        self.h5saving.save_ui(layoutright)
        
        layoutmain.addWidget(ui)
        widget = QWidget()
        widget.setLayout(layoutmain) 
        self.setCentralWidget(widget)


    def closeEvent(self, event):
        if self.pixis.connected:
            self.pixis.close()
        if self.stage.connected:
            self.stage.close()
        if self.monochromator.connected:
            self.monochromator.disconnect()
        if self.orca.connected:
            self.orca.disconnect()
            
        can_exit=True
        if can_exit:
            event.accept() # let the window close
        else:
            event.ignore()

    def heading_label(self,layout,heading_string):
        label = QLabel(heading_string)
        label.setStyleSheet("color:white;font-size: 11pt")
        layout.addWidget(label)



    def power_switch(self):
        pass





            
    