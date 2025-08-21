# coding=windows-1252
# =====================================================================
# Example how to use Tango DLL in conjunction with Python version 3.10.5
# =====================================================================
#import ctypes
import sys
#import re
from ctypes import cdll,c_int,byref,create_string_buffer,c_double,c_char_p  # import ctypes (used to call DLL functions)

import numpy as np
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel,QVBoxLayout,QPushButton


class Stage:
    def __init__(self,app):
        self.app=app
        try:
            self.m_Tango = cdll.LoadLibrary(r"C:\Users\user\Documents\Python\MicroPL\MicroPL\stage_scripts\Tango_DLL.dll")  # give location of dll (current directory)

            if self.m_Tango == 0:
                print("Error: failed to load DLL")
                sys.exit(0)

            # Tango_DLL.dll loaded successfully

            if self.m_Tango.LSX_CreateLSID == 0:
                print("unexpected error. required DLL function CreateLSID() missing")
                sys.exit(0)
            
            # continue only if required function exists

            self.LSID = c_int()
            error = int  # value is either DLL or Tango error number if not zero
            error = self.m_Tango.LSX_CreateLSID(byref(self.LSID))
            if error > 0:
                print("Error: " + str(error))
                sys.exit(0)

            # OK: got communication ID from DLL (usually 1. may vary with multiple connections)
            # keep this LSID in mind during the whole session

            if self.m_Tango.LSX_ConnectSimple == 0:
                print("unexepcted error. required DLL function ConnectSimple() missing")
                sys.exit(0)
            # continue only if required function exists

            # set your COM Port accordingly, in this example we use COM5
            # comPort = c_char_p("COM5".encode("utf-8"))
            # error = m_Tango.LSX_ConnectSimple(LSID,2,comPort,57600,0)
            # following combination of -1,"" works only for USB and PCI-E but not for RS232 connections 
            error = self.m_Tango.LSX_ConnectSimple(self.LSID, -1, "", 57600, 0)
            if error > 0:
                print("Error: LSX_ConnectSimple " + str(error))
                sys.exit(0)

            print("TANGO is now successfully connected to DLL")
            self.app.add_log("Tango connected")
            self.connected=True

            self.xpos,self.ypos=self.get_position()

        except:
            self.connected=False
            self.xpos,self.ypos=0,0
            self.app.add_log("Tango dummy mode")
            print("stage dummy mode")

        

        self.xlimit=[0.,50.]
        self.ylimit=[0.,50.]
        



        # some c-type variables (general purpose usage)
        #dx = c_double()
        #dy = c_double()
        #dz = c_double()
        #da = c_double()

        #ca = c_char()
        #cb = c_char()
        #ia = c_int()
        #ba = c_bool()

    def close(self):
        self.m_Tango.LSX_Disconnect(self.LSID)
        print("Tango disconnected")
    
    def version_DLL(self):
        
        resp = create_string_buffer(256)
        error = self.m_Tango.LSX_GetDLLVersionString(self.LSID, resp, 256)
        if error > 0:
            print("Error: DLLVersionString " + str(error))
        else:
            print("Dll version: " + str(resp.value.decode("ascii")))

    def version(self):           
        
        inp = c_char_p("?version\r".encode("utf-8"))
        resp = create_string_buffer(256)
        error = self.m_Tango.LSX_SendString(self.LSID, inp, resp, 256, True, 5000)
        if error > 0:
            print("Error: SendString " + str(error))
        else:
            print('Info: Version ' + str(resp.value.decode("ascii")))


    def get_position(self):
        dx = c_double() 
        dy = c_double()
        dz = c_double()
        da = c_double()
        # query actual position (4 axes) (unit depends on GetDimensions)
        error = self.m_Tango.LSX_GetPos(self.LSID, byref(dx), byref(dy), byref(dz), byref(da))
        
        if error > 0:
            print("Error: GetPos " + str(error))
        else:
            #print("Position = " + str(dx.value) + " " + str(dy.value) )
            return dx.value,dy.value
            #print("Position = " + str(dx.value) + " " + str(dy.value) + " " + str(dz.value) + " " + str(da.value))
            
    def set_position(self, x, y):
        # some c-type variables (general purpose usage)
        X = c_double()
        Y = c_double()     
        Z = c_double()
        A = c_double()
        X.value = x
        Y.value = y
        Z.value =  0.0
        A.value =  0.0
        error = self.m_Tango.LSX_MoveAbs(self.LSID, X, Y, Z, A, True)
        
        if error > 0:
            print("Error: Function MoveAbsolute " + str(error))
        else:
            print("Moved to " + str(X) + "," + str(Y) ) 
    
    def home_all(self):
    
        error = self.m_Tango.LSX_Calibrate(self.LSID)
        if error > 0:
            print("Error: Calibrate " + str(error))
        else:
            print("Info: Calibration done")
        # range measure for X axis
        error = self.m_Tango.LSX_RMeasureEx(self.LSID, 1)
        if error > 0:
            print("Error: Range measure " + str(error))
        else:
            print("Info: Range measure for X done")

        # range measure for Y axis
        error = self.m_Tango.LSX_RMeasureEx(self.LSID, 2)
        if error > 0:
            print("Error: Range measure " + str(error))
        else:
            print("Info: Range measure for Y done")
            
        # move center
        inp = c_char_p("!moc\r".encode("utf-8"))
        resp = create_string_buffer(256)
        error = self.m_Tango.LSX_SendString(self.LSID, inp, resp, 256, True, 5000)
        if error > 0:
            print("Error: SendString " + str(error))
        else:
            print('Info: MoveCenter via SendString done: ' + str(resp.value.decode("ascii")))

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)

    def refreshrate_edited(self,s):
        if s:
            if self.live_mode_running:
                self.refresh_rate=np.double(s)
                self.timer.stop()
                self.timer.start(int(1000*self.refresh_rate))
            else:
                self.refresh_rate=np.double(s)


    def stage_ui(self,layoutright):
        self.expanded=False
        self.app.heading_label(layoutright,"Stage     ",self.expand)
    
        self.dropdown=QVBoxLayout()
        
        layoutstage=QHBoxLayout()

        self.widgetx = QLineEdit()
        self.widgetx.setStyleSheet("background-color: lightGray")
        self.widgetx.setMaxLength(7)
        self.widgetx.setFixedWidth(self.app.standard_width)
        self.widgetx.setText(str(self.xpos))
        self.widgetx.textEdited.connect(self.stage_update_x)
        layoutstage.addWidget(self.widgetx)
        
        label = QLabel("X (mm)")
        label.setStyleSheet("color:white")
        layoutstage.addWidget(label)
        

        layoutstage.addStretch()

        self.widgety = QLineEdit()
        self.widgety.setStyleSheet("background-color: lightGray")
        self.widgety.setMaxLength(7)
        self.widgety.setFixedWidth(self.app.standard_width)
        self.widgety.setText(str(self.ypos))
        self.widgety.textEdited.connect(self.stage_update_y)
        
        label = QLabel("Y (mm)")
        label.setStyleSheet("color:white")
        layoutstage.addWidget(label)

        layoutstage.addWidget(self.widgety)       

        self.dropdown.addLayout(layoutstage)

        layoutstagebuttons=QHBoxLayout()
        self.app.normal_button(layoutstagebuttons,"GoTo",self.stage_goto)

        layoutstagebuttons.addStretch()

        self.app.normal_button(layoutstagebuttons,"Actual",self.stage_actual)        

        layoutstagebuttons.addStretch()

        self.app.normal_button(layoutstagebuttons,"Home",self.stage_home)

        self.dropdown.addLayout(layoutstagebuttons)

        layoutstagebuttons2=QHBoxLayout()
        
        
        btn=self.app.normal_button(layoutstagebuttons2,"Set Limits",self.entry_window_limits)        
        btn.setFixedWidth(110)
        layoutstagebuttons2.addStretch()

        self.dropdown.addLayout(layoutstagebuttons2)
        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)

        layoutright.addItem(self.app.vspace)


    # stage ui  methods ##########################################################
    def entry_window_limits(self):
        self.w = self.app.entrymask4(False,self.app)#device,roi
        self.w.setHeading("Stage safety limits (position in mm)")
        self.w.location_on_the_screen()
        self.w.show()
        
    def stage_actual(self):
        self.xpos,self.ypos=self.get_position()
        self.widgety.setText(str(self.ypos))
        self.widgetx.setText(str(self.xpos))
        self.widgetx.setStyleSheet("background-color: lightGray;color: black")
        self.widgety.setStyleSheet("background-color: lightGray;color: black")

        
    def stage_goto(self):
        cond1=self.xpos > self.xlimit[0]
        cond2=self.xpos < self.xlimit[1]
        cond3=self.ypos > self.ylimit[0]
        cond4=self.ypos < self.ylimit[1]

        if cond1*cond2*cond3*cond4:        
            self.set_position(self.xpos,self.ypos)    
            self.stage_actual()
            print("arrived")
        else:
            print("move aborted")
            print("point outside stage limits")
        
    def stage_update_x(self,s):
        if s:
            self.xpos=np.double(s)
            self.widgetx.setStyleSheet("background-color: lightGray;color: red")

    def stage_update_y(self,s):
        if s:
            self.ypos=np.double(s)
            self.widgety.setStyleSheet("background-color: lightGray;color: red")

    def stage_home(self):
        self.home_all()    
        self.stage_actual()
        print("stage homed")
