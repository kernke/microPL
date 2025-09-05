# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import  QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget,QLabel,QDesktopWidget,QCheckBox
from PyQt5.QtGui import QIcon

import pyqtgraph as pg
import numpy as np


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


class Multi_entry(QWidget):
    def __init__(self):
        super().__init__()

    def entry_label_structure(self,layout,widgettext,labeltext,widgetname):
        
        setattr(self,widgetname,QLineEdit())
        widget=getattr(self,widgetname)
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(50)
        widget.setText(widgettext)
        layout.addWidget(widget)

        
        labelwidget = QLabel()
        labelwidget.setStyleSheet("color:white")
        labelwidget.setText(labeltext)
        layout.addWidget(labelwidget)    

    def number_entry(self,widgetname,valuename,s,positive=True):
        if s:
            try:
                num=np.double(s)
                #if positive:
                if num<0:
                    getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:red")
                else:
                    getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:black")
                    setattr(self,valuename,num)
                #else:
                #    getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:black")
                #    setattr(self,valuename,num)
            except:
                getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:red")
                

    def p_int_entry(self,widgetname,valuename,s):
        if s:
            try:
                num=int(s)
                if num<0:
                    getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:red")
                else:
                    getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:black")
                    setattr(self,valuename,num)
            except:
                getattr(self,widgetname).setStyleSheet("background-color: lightGray;color:red")

class WarnWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warning")
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
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
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
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
        elif self.keyword=="shutter":
            self.app.pixis.shutterbtn.setText("Shutter (Normal)")
            self.app.pixis.shutter_value="Normal"
            self.app.pixis.remember_shutter="Normal"
            self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Normal')
        self.close()

    def button_b(self):
        if self.keyword=="resolution":
            self.app.orca.binning=2  
            self.app.orca.resbtn.setText("Resolution (1024)")
        elif self.keyword=="shutter":
            self.app.pixis.shutterbtn.setText("Shutter (Open)")
            self.app.pixis.shutter_value="Always Open"
            self.app.pixis.remember_shutter="Always Open"
            self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Open')
        self.close()

    def button_c(self):
        if self.keyword=="resolution":
            self.app.orca.binning=4  
            self.app.orca.resbtn.setText("Resolution (512)")
        elif self.keyword=="shutter":
            self.app.pixis.shutterbtn.setText("Shutter (Closed)")
            self.app.pixis.shutter_value="Always Closed"
            self.app.pixis.remember_shutter="Always Closed"
            self.app.pixis.cam.set_attribute_value("Shutter Timing Mode", 'Always Closed')

        self.close()

class EntryMask3(Multi_entry):
    def __init__(self,app,keyword,defaults,labels,text):
        super().__init__()
        #super(EntryMask3, self).__init__()
        self.app=app
        self.a=defaults[0]
        self.b=defaults[1]
        self.c=defaults[2]
        self.keyword=keyword

        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;") 
        self.setFixedSize(QSize(550, 200))    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        self.label.setText(text)
        layout.addWidget(self.label)

        entries=QHBoxLayout()
        widgetnames=["widgeta","widgetb","widgetc"]

        for i in range(3):            
            self.entry_label_structure(entries,str(defaults[i]),labels[i],widgetnames[i]) 
            if i<2:
                entries.addStretch()

        getattr(self,widgetnames[0]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[0],"a",s))
        getattr(self,widgetnames[1]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[1],"b",s))        
        getattr(self,widgetnames[2]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[2],"c",s))        
        
            

        layout.addLayout(entries)
        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)
        
        self.setLayout(layout)    


    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-275
        y=ag.height()//2-100
        self.move(x, y)



    def confirm_and_close(self):
        if self.keyword=="safety":
            self.app.keysight.max_voltage=self.a
            self.app.keysight.max_currentmA=self.b
            self.app.keysight.max_powermW=self.c#
        elif self.keyword=="step_size":
            if self.app.stage.step_small_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.a
            if self.app.stage.step_medium_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.b
            elif self.app.stage.step_large_micron==self.app.stage.step_size:
                self.app.stage.step_size=self.c

            self.app.stage.step_small_micron=self.a
            self.app.stage.step_medium_micron=self.b
            self.app.stage.step_large_micron=self.c
        elif self.keyword=="auto_spectral":
            self.app.pixis.auto_exposure_activated=True
            self.app.pixis.auto_expose_start=self.a
            self.app.pixis.auto_expose_min=self.b        
            self.app.pixis.auto_expose_max=self.c
            self.app.pixis.autobtn.setStyleSheet("background-color:green")
        elif self.keyword=="auto_spatial":
            if self.app.orca.live_mode_running:
                self.app.orca.timer.stop()
            self.app.orca.auto_exposure_activated=True
            self.app.orca.auto_expose_start=self.a
            self.app.orca.auto_expose_min=self.b        
            self.app.orca.auto_expose_max=self.c
            self.app.orca.autobtn.setStyleSheet("background-color:green")
            

        self.close()

class EntryMaskIV(Multi_entry):
    def __init__(self,app,keyword,defaults,labels,text):
        super().__init__()
        self.app=app
        self.keyword=keyword
        self.a=defaults[0]
        self.b=defaults[1]
        self.c=defaults[2]
        self.d=defaults[3]
        self.spatial=True
        self.spectral=True

        #self.keyword=keyword
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;") 
        self.setFixedSize(QSize(500, 350))    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        self.label.setText(text)
        layout.addWidget(self.label)

        checkboxes1=QHBoxLayout()

        checkbox = QCheckBox('Spatial image  ')
        checkbox.setStyleSheet("color:white")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self.checkbox_spatial)

        checkboxes1.addWidget(checkbox)
        checkboxes1.addStretch()

        checkbox = QCheckBox('Spectral image')
        checkbox.setStyleSheet("color:white")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self.checkbox_spectral)

        checkboxes1.addWidget(checkbox)
        checkboxes1.addStretch()

        layout.addLayout(checkboxes1)


        widgetnames=["widgeta","widgetb","widgetc","widgetd"]

        entries1=QHBoxLayout()
            
        self.entry_label_structure(entries1,str(defaults[0]),labels[0],widgetnames[0]) 
        entries1.addStretch()        
        self.entry_label_structure(entries1,str(defaults[1]),labels[1],widgetnames[1]) 
        entries1.addStretch()

        
        entries2=QHBoxLayout()
        self.entry_label_structure(entries2,str(defaults[2]),labels[2],widgetnames[2]) 
        entries2.addStretch()        
        self.entry_label_structure(entries2,str(defaults[3]),labels[3],widgetnames[3]) 
        entries2.addStretch()
        
        getattr(self,widgetnames[0]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[0],"a",s))
        getattr(self,widgetnames[1]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[1],"b",s))        
        getattr(self,widgetnames[2]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[2],"c",s))        
        getattr(self,widgetnames[3]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[3],"d",s))        


        layout.addLayout(entries1)
        layout.addLayout(entries2)
        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)
        
        self.setLayout(layout)    

    def checkbox_spatial(self,state):
        if state == 2:
            self.spatial=True
        else:
            self.spatial=False
            
    def checkbox_spectral(self,state):
        if state == 2:
            self.spectral=True
        else:
            self.spectral=False

    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-275
        y=ag.height()//2-100
        self.move(x, y)


    def confirm_and_close(self):
        if self.keyword=="set_voltages":
            self.app.scripting.IV_start_voltage=self.a
            self.app.scripting.IV_end_voltage=self.b
            self.app.scripting.IV_step_voltage=self.c
        elif self.keyword=="set_currents":
            self.app.scripting.IV_start_current_mA=self.a
            self.app.scripting.IV_end_current_mA=self.b
            self.app.scripting.IV_step_current_mA=self.c

        self.app.scripting.IV_settling_time=self.d
        self.app.scripting.IV_spatial=self.spatial
        self.app.scripting.IV_spectral=self.spectral
        self.app.scripting.script_settings_prepared=True
        self.app.scripting.btnexec.setStyleSheet("background-color:lightgrey;")
        self.app.scripting.btnstart.setStyleSheet("background-color:cyan;")
        self.close()

class EntryMask4(Multi_entry):
    def __init__(self,app,keyword,defaults,labels,text):
        super().__init__()
        self.app=app
        self.keyword=keyword

        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color: dimgray")#1e1e1e;border: 1px solid black") 
        self.setFixedSize(QSize(300, 200))

        self.xmin=defaults[0]
        self.ymin=defaults[1]
        self.xmax=defaults[2]
        self.ymax=defaults[3]
    

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        self.label.setText(text)
        layout.addWidget(self.label)


        widgetnames=["widgeta","widgetb","widgetc","widgetd"]

        entries1=QHBoxLayout()
            
        self.entry_label_structure(entries1,str(defaults[0]),labels[0],widgetnames[0]) 
        entries1.addStretch()        
        self.entry_label_structure(entries1,str(defaults[1]),labels[1],widgetnames[1]) 
        entries1.addStretch()

        
        entries2=QHBoxLayout()
        self.entry_label_structure(entries2,str(defaults[2]),labels[2],widgetnames[2]) 
        entries2.addStretch()        
        self.entry_label_structure(entries2,str(defaults[3]),labels[3],widgetnames[3]) 
        entries2.addStretch()
        
        getattr(self,widgetnames[0]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[0],"xmin",s))
        getattr(self,widgetnames[1]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[1],"ymin",s))        
        getattr(self,widgetnames[2]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[2],"xmax",s))        
        getattr(self,widgetnames[3]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[3],"ymax",s))        



        layout.addLayout(entries1)
        layout.addLayout(entries2)

        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)

        self.setLayout(layout)    

    
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-150
        y=ag.height()//2-100
        self.move(x, y)

    def confirm_and_close(self):

        if self.keyword=="roi": #ROI
            self.app.pixis.roi.setPos(pg.Point([self.xmin,self.ymin]))
            deltax=self.xmax-self.xmin
            deltay=self.ymax-self.ymin
            self.app.pixis.roi.setSize([deltax,deltay])
        else: #stage
            self.app.stage.xlimit=[self.xmin,self.xmax]
            self.app.stage.ylimit=[self.ymin,self.ymax]
            
        self.close()

class EntryMaskMapping(Multi_entry):
    def __init__(self,app,defaults,labels,text):
        super().__init__()
        self.app=app
        self.setWindowTitle("Enter Values")
        self.setWindowIcon(QIcon(r"C:\Users\user\Documents\Python\microPL\MicroPL/Logo.png"))
        #self.setWindowIcon(QIcon('MicroPL/Logo.png'))
        self.setStyleSheet("background-color:dimgray")# #1e1e1e;") 
        self.setFixedSize(QSize(500, 350))

        self.xmin=defaults[0]
        self.ymin=defaults[1]
        self.xmax=defaults[2]
        self.ymax=defaults[3]
        self.xnum=defaults[4]
        self.ynum=defaults[5]

        self.spatial=True
        self.spectral=False
                
        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setText(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("color:white")
        layout.addWidget(self.label)

        checkboxes1=QHBoxLayout()

        checkbox = QCheckBox('Spatial image  ')
        checkbox.setStyleSheet("color:white")
        checkbox.setChecked(True)
        checkbox.stateChanged.connect(self.checkbox_spatial)

        checkboxes1.addWidget(checkbox)
        checkboxes1.addStretch()

        checkbox = QCheckBox('Spectral image')
        checkbox.setStyleSheet("color:white")
        checkbox.setChecked(False)
        checkbox.stateChanged.connect(self.checkbox_spectral)

        checkboxes1.addWidget(checkbox)
        checkboxes1.addStretch()

        layout.addLayout(checkboxes1)


        widgetnames=["widgeta","widgetb","widgetc","widgetd","widgete","widgetf"]

        entries1=QHBoxLayout()            
        self.entry_label_structure(entries1,str(defaults[0]),labels[0],widgetnames[0]) 
        entries1.addStretch()        
        self.entry_label_structure(entries1,str(defaults[1]),labels[1],widgetnames[1]) 
        entries1.addStretch()

        entries2=QHBoxLayout()
        self.entry_label_structure(entries2,str(defaults[2]),labels[2],widgetnames[2]) 
        entries2.addStretch()        
        self.entry_label_structure(entries2,str(defaults[3]),labels[3],widgetnames[3]) 
        entries2.addStretch()
        
        entries3=QHBoxLayout()
        self.entry_label_structure(entries3,str(defaults[4]),labels[4],widgetnames[4]) 
        entries3.addStretch()        
        self.entry_label_structure(entries3,str(defaults[5]),labels[5],widgetnames[5]) 
        entries3.addStretch()

        getattr(self,widgetnames[0]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[0],"xmin",s))
        getattr(self,widgetnames[1]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[1],"ymin",s))        
        getattr(self,widgetnames[2]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[2],"xmax",s))        
        getattr(self,widgetnames[3]).textEdited.connect(
                lambda s: self.number_entry(widgetnames[3],"ymax",s))        

        getattr(self,widgetnames[4]).textEdited.connect(
                lambda s: self.p_int_entry(widgetnames[4],"xnum",s))        
        getattr(self,widgetnames[5]).textEdited.connect(
                lambda s: self.p_int_entry(widgetnames[5],"ynum",s))        

        layout.addLayout(entries1)
        layout.addLayout(entries2)
        layout.addLayout(entries3)

        layoutclosing=QHBoxLayout()
        layoutclosing.addStretch()
        normal_button(layoutclosing,"Confirm",self.confirm_and_close)
        layoutclosing.addStretch()
        layout.addLayout(layoutclosing)
        self.setLayout(layout)    
    
    def location_on_the_screen(self):
        ag = QDesktopWidget().availableGeometry()
        x=ag.width()//2-175
        y=ag.height()//2-150
        self.move(x, y)

    def checkbox_spatial(self,state):
        if state == 2:
            self.spatial=True
            print("spat True")
        else:
            self.spatial=False
            
    def checkbox_spectral(self,state):
        if state == 2:
            self.spectral=True
        else:
            self.spectral=False

    def confirm_and_close(self):
        self.app.scripting.script_x_entries=[self.xmin,self.xmax,int(self.xnum)]
        self.app.scripting.script_y_entries=[self.ymin,self.ymax,int(self.ynum)]

        xcoords=np.linspace(self.xmin,self.xmax,int(self.xnum))
        ycoords=np.linspace(self.ymin,self.ymax,int(self.ynum))
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

        self.app.scripting.grid_spatial=self.spatial
        self.app.scripting.grid_spectral=self.spectral        
        self.app.scripting.script_positions_x=newx
        self.app.scripting.script_positions_y=newy  
        self.app.scripting.script_settings_prepared=True
        self.app.scripting.btnexec.setStyleSheet("background-color:lightgrey;")
        self.app.scripting.btnstart.setStyleSheet("background-color:cyan;")
        self.close()