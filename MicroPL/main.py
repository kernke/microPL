# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThreadPool   
# from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget,QLabel,QScrollArea

from .Application.gui_utility import EntryMask4,EntryMask6,WarnWindow,normal_button,set_layout_visible,heading_label
from .Application.saving import Saving
from .Application.scripting import Scripting
from .Pixis.cam import Pixis
from .stage_scripts.stage import Stage
from .SCT320_Wrapper.mono import SCT320
from .Hamamatsu.orca import Orca
from .Keysight.power_supply import Keysight

#color_text_on_dark="white"
#color_text_on_bright="black"
#color_interactive_stuff="lightGray"
#color_background="black"
          
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MicroPL App")
        self.setStyleSheet("background-color: black;")#black 
        self.move(160,32)
        self.resize(1536,900)
               
        self.standard_width=55
        self.normal_button=normal_button
        self.set_layout_visible=set_layout_visible
        self.heading_label=heading_label

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
        self.keysight=Keysight(self)
        
        self.metadata_spatial=dict()
        self.metadata_spatial["unsaved"]=True

        self.metadata_spectral=dict()
        self.metadata_spectral["unsaved"]=True
        
        self.metadata_electrical=dict()
        self.metadata_electrical["unsaved"]=True

        layoutmain = QHBoxLayout() # whole window
        layoutright = QVBoxLayout() # right side containing image,colorbar and 1D-roi-plot
        layoutleft = QVBoxLayout() # left side containing all the buttons
        layoutlefth1=QHBoxLayout()
        layoutlefth2=QHBoxLayout() 


        # graphics show
        self.orca.spatial_camera_show(layoutlefth1)
        #image and colorbar

        self.pixis.spectral_camera_show(layoutlefth2)
        #image, colorbar and 1D-profile plot

        layoutleft.addLayout(layoutlefth1,4)
        layoutleft.addLayout(layoutlefth2,3)

        layoutmain.addLayout( layoutleft )

        # user interface buttons 
        scroll = QScrollArea()
        scroll.setFixedWidth(330)
        ui= QWidget() 
        ui.setFixedWidth(300)
        ui.setLayout(layoutright)

        self.orca.spatial_camera_ui(layoutright)

        self.pixis.spectral_camera_ui(layoutright)
        
        self.monochromator.mono_ui(layoutright)

        self.stage.stage_ui(layoutright)

        self.keysight.power_ui(layoutright)

        self.scripting.script_ui(layoutright)

        self.h5saving.save_ui(layoutright)
        
        scroll.setWidgetResizable(True)
        scroll.setWidget(ui)


        layoutmain.addWidget(scroll)#ui
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

        






            
    