# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThreadPool,QStringListModel 
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QWidget,QLabel
from PyQt5.QtWidgets import QScrollArea,QListView,QSpacerItem,QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon 
#import os

from .Application.gui_utility import ButtonMask3,EntryMask3,EntryMask4,EntryMaskMapping,WarnWindow
from .Application.gui_utility import EntryMaskIV,normal_button,set_layout_visible,heading_label

from .Application.saving import Saving
from .Application.scripting import Scripting,Sleep_Worker
from .Pixis.cam import Pixis
from .stage_scripts.stage import Stage
from .SCT320_Wrapper.mono import SCT320
from .Hamamatsu.orca import Orca
from .Keysight.power_supply import Keysight
from .Switcher.relais_switcher import Switcher

#color_text_on_dark="white"
#color_text_on_bright="black"
#color_interactive_stuff="lightGray"
#color_background="#1e1e1e" #dark gray
          
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MicroPL App")

        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))#'MicroPL/Logo.png'))
        #print(os.listdir())
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

        self.warnwindow=WarnWindow
        self.buttonmask3=ButtonMask3
        self.entrymask3=EntryMask3
        self.entrymask4=EntryMask4
        self.entrymaskiv=EntryMaskIV
        self.entrymaskmapping=EntryMaskMapping
        self.sleep_worker_class=Sleep_Worker
        self.vspace = QSpacerItem(0, 20, QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.threadpool = QThreadPool() 
        
        # initialize all subclasses, such that they exist as instances inside MainWindow
        self.h5saving=Saving(self)
        self.scripting=Scripting(self)

        self.stage = Stage(self)
        self.monochromator=SCT320(self)
        self.pixis = Pixis(self)
        self.orca = Orca(self)
        self.switcher=Switcher(self)
        self.keysight=Keysight(self)

        #        
        self.metadata_spatial=dict()
        self.metadata_spatial["unsaved"]=True

        self.metadata_spectral=dict()
        self.metadata_spectral["unsaved"]=True
        
        self.metadata_timeline=dict()
        self.metadata_timeline["unsaved"]=True

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

        self.status_orca = QLabel("Spatial Max: \nSpatial Median: ")
        self.status_orca.setStyleSheet(status_style_string)
        layoutstatus.addWidget(self.status_orca)

        layoutstatus.addItem(self.vspace)

        self.status_pixis = QLabel("Spectral Max: \n95th percentile: \nROI Max at: ")
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

        msg = QMessageBox(self)
        msg.setWindowTitle("Close MicroPL")
        msg.setText("Are you sure you want to close the software?")
        msg.setIcon(QMessageBox.Question)

        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)

        # Style message box
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e1e;
            }

            QMessageBox QLabel {
                color: white;
                background-color: transparent;
            }
        """)

        # Explicitly style the buttons
        button_style = """
            QPushButton {
                color: white;
                background-color: #606060;
                border: 1px solid #909090;
                border-radius: 4px;
                min-width: 80px;
                min-height: 28px;
                padding: 4px 12px;
            }

            QPushButton:hover {
                background-color: #808080;
            }

            QPushButton:pressed {
                background-color: #505050;
            }
        """

        msg.button(QMessageBox.Yes).setStyleSheet(button_style)
        msg.button(QMessageBox.No).setStyleSheet(button_style)

        reply = msg.exec_()

        if reply == QMessageBox.Yes:

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

            if self.switcher.connected:
                self.switcher.disconnect()

            event.accept()

        else:
            event.ignore()

        
    def add_log(self,logstring):
        self.logging_list.insert(0, logstring)
        self.logging_model.setStringList(self.logging_list)
        if len(self.logging_list)>2000:
            del self.logging_list[-1]

    def update_log(self,logstring):
        del self.logging_list[0]
        self.logging_list.insert(0, logstring)
        self.logging_model.setStringList(self.logging_list)




            
    