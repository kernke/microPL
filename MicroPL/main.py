# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThreadPool,QStringListModel 
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget,QLabel,QScrollArea,QListView,QSpacerItem,QSizePolicy

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
#color_background="#1e1e1e" #dark gray
          
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MicroPL App")
        self.setStyleSheet("background-color: #1e1e1e;")
        self.move(0,0)
        self.resize(1920,980)

        self.logging_list=[]      
        self.logging_model = QStringListModel()
        self.logging_model.setStringList(self.logging_list) 
        self.standard_width=55
        self.normal_button=normal_button
        self.set_layout_visible=set_layout_visible
        self.heading_label=heading_label
        self.temporary_3values=None

        self.warnwindow=WarnWindow
        self.entrymask4=EntryMask4
        self.entrymask6=EntryMask6
        self.vspace = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.threadpool = QThreadPool() 
        
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
        layoutleft=QVBoxLayout() # left containing info and log
        layoutmidleft = QVBoxLayout() # midleft containing navigation and timeline/IV-curve
        layoutmidright = QVBoxLayout() # midright containing images,colorbars and 1D-roi-plot
        layoutright = QVBoxLayout() # right side containing all the buttons

        left_ui= QWidget() 
        left_ui.setFixedWidth(270)
        left_ui.setLayout(layoutleft)

        layoutstatus=QVBoxLayout()

        label = QLabel("Status")
        label.setStyleSheet("background-color: #1e1e1e;color:white;font-size: 15pt")
        layoutstatus.addWidget(label)

        layoutstatus.addItem(self.vspace)

        status_style_string="background-color: #1e1e1e;color:white;font-size: 13pt"
        stage_status_string="Stage X: "+str(self.stage.xpos)+ " mm\n"
        stage_status_string+="Stage Y: "+str(self.stage.ypos)+ " mm"
        self.status_stage = QLabel(stage_status_string)
        self.status_stage.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_stage)

        layoutstatus.addItem(self.vspace)

        power_status_string="Voltage: "+str(self.keysight.voltage)+" V\nCurrent: "+str(self.keysight.current)+" mA"
        self.status_electric = QLabel(power_status_string)
        self.status_electric.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_electric)
        
        layoutstatus.addItem(self.vspace)

        self.status_orca = QLabel("Spatial Max: \nSpatial Mean: ")
        self.status_orca.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_orca)

        layoutstatus.addItem(self.vspace)

        self.status_pixis = QLabel("Spectral Max: \nROI Max at: ")
        self.status_pixis.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_pixis)


        self.status_mono=QLabel("from: \nto: ")
        self.status_mono.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_mono)

        layoutstatus.addStretch()
        
        # weird behavior 
        label = QLabel("")  
        layoutstatus.addWidget(label)
        ################

        layoutleft.addLayout(layoutstatus)

        layoutlog=QVBoxLayout()

        layoutlog.addWidget(label)
        label = QLabel("Logging")
        label.setStyleSheet("background-color: #1e1e1e;color:white;font-size: 11pt")

        layoutlog.addWidget(label)

        list_view = QListView()
        list_view.setModel(self.logging_model)
        list_view.setStyleSheet("""
            QListView {
                background-color: #1e1e1e;   /* Dark background */
                color: white;               /* Default text color */
                font-family: Consolas;
                font-size: 10pt;
            }
            QListView::item:selected {
                background-color: #0078d7;  /* Highlight color */
                color: white;
            }
        """)

        layoutlog.addWidget(list_view)
        layoutleft.addLayout(layoutlog)

        layoutmain.addWidget( left_ui )

        self.midleft= QWidget() 
        self.midleft.setLayout(layoutmidleft)

        self.stage.navigation_graphics_show(layoutmidleft)
        self.keysight.power_graphics_show(layoutmidleft)

        layoutmain.addWidget(self.midleft)

        self.midright= QWidget() 
        self.midright.setLayout(layoutmidright)

        # graphics show
        self.orca.spatial_camera_show(layoutmidright)
        #image and colorbar

        self.pixis.spectral_camera_show(layoutmidright)
        #image, colorbar and 1D-profile plot


        layoutmain.addWidget( self.midright)

        # user interface buttons 
        scroll = QScrollArea()
        scroll.setFixedWidth(330)
        ui= QWidget() 
        ui.setFixedWidth(310)
        ui.setLayout(layoutright)

        self.h5saving.save_ui(layoutright)

        self.orca.spatial_camera_ui(layoutright)

        self.pixis.spectral_camera_ui(layoutright)
        
        self.monochromator.mono_ui(layoutright)

        self.keysight.power_ui(layoutright)

        self.keysight.timeline_ui(layoutright)

        self.stage.stage_ui(layoutright)

        self.scripting.script_ui(layoutright)



        
        layoutright.addStretch()
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
        if self.keysight.connected:
            self.keysight.disconnect()    
        
        can_exit=True
        if can_exit:
            event.accept() # let the window close
        else:
            event.ignore()

        
    def add_log(self,logstring):
        self.logging_list.insert(0, logstring)
        self.logging_model.setStringList(self.logging_list)
        if len(self.logging_list)>2000:
            del self.logging_list[-1]





            
    