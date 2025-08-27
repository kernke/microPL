# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget,QLabel,QDesktopWidget,QDialog
from PyQt5.QtGui import QIcon

import pyqtgraph as pg
import numpy as np

#from .utility import normal_button


def normal_button(layout,text,function):
    button = QPushButton(text)
    button.setStyleSheet("background-color: lightGray")
    button.clicked.connect(function)
    button.setFixedWidth(70)

    layout.addWidget(button)
    return button

def set_layout_visible(layout, visible):
    """Recursively hide or show all widgets in a layout (handles nested layouts)."""
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.widget():  # direct widget
            item.widget().setVisible(visible)
        elif item.layout():  # nested layout
            set_layout_visible(item.layout(), visible)

def heading_label(layout,heading_string,func_connect):

    layoutheading=QHBoxLayout()
    button = QPushButton("▽ "+heading_string)
    button.setStyleSheet("background-color: #1e1e1e;color:white;font-size: 11pt")
    button.clicked.connect(func_connect)
    button.setFlat(True)
    layoutheading.addWidget(button)
    layoutheading.addStretch()
    layout.addLayout(layoutheading)


class WarnWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warning")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")
        self.setFixedSize(QSize(300, 150))
        button = QPushButton("Close")
        button.clicked.connect(self.close)
        layout = QVBoxLayout()
        self.label = QLabel()
        layout.addWidget(self.label)
        layout.addWidget(button)
        self.setLayout(layout)

    def setWarnText(self,text):
        self.label.setText(text)

    
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-150
        y=ag.height()//2-75
        self.move(x, y)

class ButtonMask3(QWidget):
    def __init__(self,app,optionslist,keyword):
        super().__init__()
        self.app=app
        self.keyword=keyword
        self.setWindowTitle("Choose")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")##1e1e1e;") 
        self.setFixedSize(QSize(350, 200))    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)
        self.selected=None

        layoutbuttons=QHBoxLayout()
        layoutbuttons.addStretch()
        btn=normal_button(layoutbuttons,optionslist[0],self.button_a)
        btn.setFixedWidth(80)
        layoutbuttons.addStretch()
        btn=normal_button(layoutbuttons,optionslist[1],self.button_b)
        btn.setFixedWidth(80)
        layoutbuttons.addStretch()
        btn=normal_button(layoutbuttons,optionslist[2],self.button_c)
        btn.setFixedWidth(80)
        layoutbuttons.addStretch()
        
        layout.addLayout(layoutbuttons)

        
        self.setLayout(layout)    

    def setHeading(self,text):
        self.label.setText(text)

    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-150
        y=ag.height()//2-100
        self.move(x, y)

    def button_a(self):
        if self.keyword=="resolution":
            self.app.orca.binning=1  
            self.app.orca.resbtn.setText("Resolution (2048)")
        self.close()

    def button_b(self):
        if self.keyword=="resolution":
            self.app.orca.binning=2  
            self.app.orca.resbtn.setText("Resolution (1024)")
        self.close()

    def button_c(self):
        if self.keyword=="resolution":
            self.app.orca.binning=4  
            self.app.orca.resbtn.setText("Resolution (512)")
        self.close()



class EntryMask3(QWidget):
    def __init__(self,app,keyword):
        super().__init__()
        self.app=app
        self.keyword=keyword
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;") 
        self.setFixedSize(QSize(550, 200))    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)

        entries=QHBoxLayout()
        #entries.addStretch()

        self.widgeta = QLineEdit()
        self.widgeta.setStyleSheet("background-color: lightGray")
        self.widgeta.setMaxLength(5)
        self.widgeta.setFixedWidth(50)
        self.widgeta.textEdited.connect(self.temporary_a)
        entries.addWidget(self.widgeta)
        
        self.labela = QLabel()
        self.labela.setStyleSheet("color:white")
        entries.addWidget(self.labela)    
        entries.addStretch()
        
        self.widgetb = QLineEdit()
        self.widgetb.setStyleSheet("background-color: lightGray")
        self.widgetb.setMaxLength(5)
        self.widgetb.setFixedWidth(50)
        self.widgetb.textEdited.connect(self.temporary_b)
        entries.addWidget(self.widgetb)
        
        self.labelb = QLabel()
        self.labelb.setStyleSheet("color:white")
        entries.addWidget(self.labelb)    
        entries.addStretch()

        self.widgetc = QLineEdit()
        self.widgetc.setStyleSheet("background-color: lightGray")
        self.widgetc.setMaxLength(5)
        self.widgetc.setFixedWidth(50)
        self.widgetc.textEdited.connect(self.temporary_c)
        entries.addWidget(self.widgetc)
        
        self.labelc = QLabel()
        self.labelc.setStyleSheet("color:white")
        entries.addWidget(self.labelc)    
        #entries.addStretch()
                
        layout.addLayout(entries)
        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)
        
        self.setLayout(layout)    

    def setHeading(self,text):
        self.label.setText(text)

    def setLabels(self,labels):
        self.labela.setText(labels[0])
        self.labelb.setText(labels[1])
        self.labelc.setText(labels[2])

    def setDefaults(self,defaults):
        self.widgeta.setText(defaults[0])
        self.a=defaults[0]
        self.widgetb.setText(defaults[1])
        self.b=defaults[1]
        self.widgetc.setText(defaults[2])
        self.c=defaults[2]

    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-275
        y=ag.height()//2-100
        self.move(x, y)

    def temporary_a(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.a=np.double(s)
        
    def temporary_b(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.b=np.double(s)

    def temporary_c(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.c=np.double(s)


    def confirm_and_close(self):
        if self.keyword=="safety":
            self.app.keysight.max_voltage=self.a
            self.app.keysight.max_currentmA=self.b
            self.app.keysight.max_powermW=self.c#
        if self.keyword=="step_size":
            if self.app.stage.step_small_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.a
            if self.app.stage.step_medium_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.b
            elif self.app.stage.step_large_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.c

            self.app.stage.step_small_micron=self.a
            self.app.stage.step_medium_micron=self.b
            self.app.stage.step_large_micron=self.c
           
        self.close()


class EntryMask4b(QWidget):
    def __init__(self,app,keyword):
        super().__init__()
        self.app=app
        self.keyword=keyword
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;") 
        self.setFixedSize(QSize(500, 250))    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)

        entries1=QHBoxLayout()
        #entries.addStretch()

        self.widgeta = QLineEdit()
        self.widgeta.setStyleSheet("background-color: lightGray")
        self.widgeta.setMaxLength(5)
        self.widgeta.setFixedWidth(50)
        self.widgeta.textEdited.connect(self.temporary_a)
        entries1.addWidget(self.widgeta)
        
        self.labela = QLabel()
        self.labela.setStyleSheet("color:white")
        entries1.addWidget(self.labela)    
        entries1.addStretch()
        
        self.widgetb = QLineEdit()
        self.widgetb.setStyleSheet("background-color: lightGray")
        self.widgetb.setMaxLength(5)
        self.widgetb.setFixedWidth(50)
        self.widgetb.textEdited.connect(self.temporary_b)
        entries1.addWidget(self.widgetb)
        
        self.labelb = QLabel()
        self.labelb.setStyleSheet("color:white")
        entries1.addWidget(self.labelb)    
        entries1.addStretch()
        
        entries2=QHBoxLayout()
        

        self.widgetc = QLineEdit()
        self.widgetc.setStyleSheet("background-color: lightGray")
        self.widgetc.setMaxLength(5)
        self.widgetc.setFixedWidth(50)
        self.widgetc.textEdited.connect(self.temporary_c)
        entries2.addWidget(self.widgetc)
        
        self.labelc = QLabel()
        self.labelc.setStyleSheet("color:white")
        entries2.addWidget(self.labelc)    
        #entries.addStretch()

        self.widgetd = QLineEdit()
        self.widgetd.setStyleSheet("background-color: lightGray")
        self.widgetd.setMaxLength(5)
        self.widgetd.setFixedWidth(50)
        self.widgetd.textEdited.connect(self.temporary_d)
        entries2.addWidget(self.widgetd)
        
        self.labeld = QLabel()
        self.labeld.setStyleSheet("color:white")
        entries2.addWidget(self.labeld)    


        layout.addLayout(entries1)
        layout.addLayout(entries2)
        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)
        
        self.setLayout(layout)    

    def setHeading(self,text):
        self.label.setText(text)

    def setLabels(self,labels):
        self.labela.setText(labels[0])
        self.labelb.setText(labels[1])
        self.labelc.setText(labels[2])
        self.labeld.setText(labels[3])

    def setDefaults(self,defaults):
        self.widgeta.setText(defaults[0])
        self.a=defaults[0]
        self.widgetb.setText(defaults[1])
        self.b=defaults[1]
        self.widgetc.setText(defaults[2])
        self.c=defaults[2]
        self.widgetd.setText(defaults[3])
        self.d=defaults[3]

    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-275
        y=ag.height()//2-100
        self.move(x, y)

    def temporary_a(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.a=np.double(s)
        
    def temporary_b(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.b=np.double(s)

    def temporary_c(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.c=np.double(s)

    def temporary_d(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.d=np.double(s)


    def confirm_and_close(self):
        if self.keyword=="IVcurve":
            self.app.keysight.IV_start_voltage=self.a
            self.app.keysight.IV_end_voltage=self.b
            self.app.keysight.IV_step_voltage=self.c
            self.app.keysight.IV_settling_time=self.d
            self.app.keysight.acqivbtn.setStyleSheet("background-color:cyan")
            self.app.keysight.IV_settings_prepared=True
        self.close()


class EntryMask4(QWidget):
    def __init__(self,check_bool,app):
        super().__init__()
        self.device=app.stage
        self.roi=app.pixis.roi
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;border: 1px solid black") 
        self.setFixedSize(QSize(300, 200))
        if check_bool:
            self.tempo_xmin=int(self.roi.pos()[0])
            self.tempo_ymin=int(self.roi.pos()[1])
            self.tempo_xmax=int(self.roi.pos()[0]+self.roi.size()[0])
            self.tempo_ymax=int(self.roi.pos()[1]+self.roi.size()[1])
        else:
            self.tempo_xmin=self.device.xlimit[0]
            self.tempo_ymin=self.device.ylimit[0]
            self.tempo_xmax=self.device.xlimit[1]
            self.tempo_ymax=self.device.ylimit[1]
    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)

        entry_min=QHBoxLayout()
        entry_max=QHBoxLayout()

        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_xmin))
        widget.textEdited.connect(self.temporary_xmin)
        entry_min.addWidget(widget)
        
        label = QLabel("X min")
        label.setStyleSheet("color:white")
        entry_min.addWidget(label)    
        entry_min.addStretch()
        
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_ymin))
        widget.textEdited.connect(self.temporary_ymin)
        entry_min.addWidget(widget)
        
        label = QLabel("Y min")
        label.setStyleSheet("color:white")
        entry_min.addWidget(label)    


        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_xmax))
        widget.textEdited.connect(self.temporary_xmax)
        entry_max.addWidget(widget)
        
        label = QLabel("X max")
        label.setStyleSheet("color:white")
        entry_max.addWidget(label)    
        entry_max.addStretch()
        
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_ymax))
        widget.textEdited.connect(self.temporary_ymax)
        entry_max.addWidget(widget)
        
        label = QLabel("Y max")
        label.setStyleSheet("color:white")
        entry_max.addWidget(label)    
        
        layout.addLayout(entry_min)
        layout.addLayout(entry_max)

        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",lambda: self.confirm_and_close(check_bool))
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)

        self.setLayout(layout)    

    def setHeading(self,text):
        self.label.setText(text)

    
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-150
        y=ag.height()//2-100
        self.move(x, y)

    def temporary_xmin(self,s):
        if s:
            self.tempo_xmin=np.double(s)
        
    def temporary_ymin(self,s):
        if s:
            self.tempo_ymin=np.double(s)

    def temporary_xmax(self,s):
        if s:
            self.tempo_xmax=np.double(s)

    def temporary_ymax(self,s):
        if s:
            self.tempo_ymax=np.double(s)

    def confirm_and_close(self,check_bool):
        if check_bool: #ROI
            self.roi.setPos(pg.Point([self.tempo_xmin,self.tempo_ymin]))
            deltax=self.tempo_xmax-self.tempo_xmin
            deltay=self.tempo_ymax-self.tempo_ymin
            self.roi.setSize([deltax,deltay])
        else: #stage
            self.device.xlimit=[self.tempo_xmin,self.tempo_xmax]
            self.device.ylimit=[self.tempo_ymin,self.tempo_ymax]
            
        self.close()



class EntryMask6(QDialog):

    def __init__(self,app):
        super().__init__()
        self.app=app
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color:dimgray")# #1e1e1e;") 
        self.setFixedSize(QSize(350, 300))

        if self.app.scripting.script_x_entries is None:
            self.tempo_xmin=0.
            self.tempo_ymin=0.
            self.tempo_xmax=50.
            self.tempo_ymax=50.
            self.tempo_xnum=10
            self.tempo_ynum=10
            self.app.scripting.script_x_entries=[self.tempo_xmin,self.tempo_xmax,int(self.tempo_xnum)]
            self.app.scripting.script_y_entries=[self.tempo_ymin,self.tempo_ymax,int(self.tempo_ynum)]
        else:
            self.tempo_xmin=self.app.scripting.script_x_entries[0]
            self.tempo_ymin=self.app.scripting.script_y_entries[0]
            self.tempo_xmax=self.app.scripting.script_x_entries[1]
            self.tempo_ymax=self.app.scripting.script_y_entries[1]
            self.tempo_xnum=self.app.scripting.script_x_entries[2]
            self.tempo_ynum=self.app.scripting.script_y_entries[2]
        

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setText("Measurement grid with current settings\nChoose the grid via start position (min), end position (max)\nand number of points (num) in each dimension")
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)

        entry_min=QHBoxLayout()
        entry_max=QHBoxLayout()
        entry_num=QHBoxLayout()

        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_xmin))
        widget.textEdited.connect(self.temporary_xmin)
        entry_min.addWidget(widget)
        
        label = QLabel("X min")
        label.setStyleSheet("color:white")
        entry_min.addWidget(label)    
        entry_min.addStretch()
        
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_ymin))
        widget.textEdited.connect(self.temporary_ymin)
        entry_min.addWidget(widget)
        
        label = QLabel("Y min")
        label.setStyleSheet("color:white")
        entry_min.addWidget(label)    


        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_xmax))
        widget.textEdited.connect(self.temporary_xmax)
        entry_max.addWidget(widget)
        
        label = QLabel("X max")
        label.setStyleSheet("color:white")
        entry_max.addWidget(label)    
        entry_max.addStretch()
        
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_ymax))
        widget.textEdited.connect(self.temporary_ymax)
        entry_max.addWidget(widget)
        
        label = QLabel("Y max")
        label.setStyleSheet("color:white")
        entry_max.addWidget(label)    
        
        layout.addLayout(entry_min)
        layout.addLayout(entry_max)


        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_xnum))
        widget.textEdited.connect(self.temporary_xnum)
        entry_num.addWidget(widget)
        
        label = QLabel("X num")
        label.setStyleSheet("color:white")
        entry_num.addWidget(label)    
        entry_num.addStretch()
        
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(self.tempo_ynum))
        widget.textEdited.connect(self.temporary_ynum)
        entry_num.addWidget(widget)
        
        label = QLabel("Y num")
        label.setStyleSheet("color:white")
        entry_num.addWidget(label)    

        layout.addLayout(entry_num)

        normal_button(layout,"Start",self.confirm_and_close)
        self.setLayout(layout)    
    
    
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-175
        y=ag.height()//2-150
        self.move(x, y)

    def temporary_xmin(self,s):
        if s:
            self.tempo_xmin=np.double(s)
            self.app.scripting.script_x_entries[0]=self.tempo_xmin
        
    def temporary_ymin(self,s):
        if s:
            self.tempo_ymin=np.double(s)
            self.app.scripting.script_y_entries[0]=self.tempo_ymin

    def temporary_xmax(self,s):
        if s:
            self.tempo_xmax=np.double(s)
            self.app.scripting.script_x_entries[1]=self.tempo_xmax

    def temporary_ymax(self,s):
        if s:
            self.tempo_ymax=np.double(s)
            self.app.scripting.script_y_entries[1]=self.tempo_ymax

    def temporary_xnum(self,s):
        if s:
            self.tempo_xnum=int(s)
            self.app.scripting.script_x_entries[2]=self.tempo_xnum

    def temporary_ynum(self,s):
        if s:
            self.tempo_ynum=int(s)
            self.app.scripting.script_y_entries[2]=self.tempo_ynum

            
    def confirm_and_close(self):
        xcoords=np.linspace(self.tempo_xmin,self.tempo_xmax,int(self.tempo_xnum))
        ycoords=np.linspace(self.tempo_ymin,self.tempo_ymax,int(self.tempo_ynum))
        xx,yy=np.meshgrid(xcoords,ycoords)

        newx=np.zeros(xx.shape[0]*xx.shape[1])
        newy=np.zeros(yy.shape[0]*yy.shape[1])
        counter=0
        orderbool=True
        for i in range(xx.shape[0]):
            orderbool=not orderbool
            for j in range(xx.shape[1]):
                if orderbool:
                    jnum=xx.shape[1]-1-j
                else:
                    jnum=j        
                newx[counter]=xx[i,jnum]
                newy[counter]=yy[i,jnum]
                counter+=1
        
        self.app.scripting.script_positions_x=newx
        self.app.scripting.script_positions_y=newy  
        self.app.scripting.script_execution=True
        self.close()