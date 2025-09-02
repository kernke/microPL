# coding=windows-1252
# =====================================================================
# Example how to use Tango DLL in conjunction with Python version 3.10.5
# =====================================================================
#import ctypes
import sys
#import re
from ctypes import cdll,c_int,byref,create_string_buffer,c_double,c_char_p  # import ctypes (used to call DLL functions)
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QHBoxLayout,  QLineEdit,QLabel,QVBoxLayout,QPushButton,QComboBox,QApplication
from PyQt5.QtCore import pyqtSignal, QTimer,QRunnable,pyqtSlot,QObject

class Update_Signal(QObject):

    string_update = pyqtSignal(object)   
    #complete_signal=pyqtSignal(bool)

class Status_update(QRunnable):

    def __init__(self, stage,event=None):
        super().__init__()
        self.stage = stage
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params
        x,y =self.stage.get_position()
        stage_status_string="Stage X: "+str(x)+ " mm\n"
        stage_status_string+="Stage Y: "+str(y)+ " mm"

        self.signals.string_update.emit((stage_status_string,x,y))
        if self.event:
            self.event.set()
        #self.signals.complete_signal.emit(True)
 

class Homing(QRunnable):
    def __init__(self, stageclass,event=None):
        super().__init__()
        self.stageclass = stageclass
        self.signals=Update_Signal()
        self.event=event

    @pyqtSlot()
    def run(self): # A slot takes no params

        error = self.stageclass.m_Tango.LSX_Calibrate(self.LSID)
        if error > 0:
            print("Error: Calibrate " + str(error))
        else:
            print("Info: Calibration done")
        # range measure for X axis
        error = self.stageclass.m_Tango.LSX_RMeasureEx(self.LSID, 1)
        if error > 0:
            print("Error: Range measure " + str(error))
        else:
            print("Info: Range measure for X done")

        # range measure for Y axis
        error = self.stageclass.m_Tango.LSX_RMeasureEx(self.LSID, 2)
        if error > 0:
            print("Error: Range measure " + str(error))
        else:
            print("Info: Range measure for Y done")
            
        # move center
        inp = c_char_p("!moc\r".encode("utf-8"))
        resp = create_string_buffer(256)
        error = self.stageclass.m_Tango.LSX_SendString(self.LSID, inp, resp, 256, True, 5000)
        if error > 0:
            print("Error: SendString " + str(error))
        else:
            print('Info: MoveCenter via SendString done: ' + str(resp.value.decode("ascii")))

        x,y =self.stageclass.stage.get_position()
        stage_status_string="Stage X: "+str(x)+ " mm\n"
        stage_status_string+="Stage Y: "+str(y)+ " mm"


        self.signals.string_update.emit((stage_status_string,x,y))
        if self.event:
            self.event.set()
        #self.signals.complete_signal.emit(True)

class Stage:
    def __init__(self,app):
        self.app=app
        try:
            self.m_Tango = cdll.LoadLibrary(r"C:\Users\user\Documents\Python\MicroPL\MicroPL\stage_scripts\Tango_DLL.dll")  # give location of dll (current directory)
            testing=False
            if testing:
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
            else:
                self.LSID = c_int()
                error = self.m_Tango.LSX_CreateLSID(byref(self.LSID))
                error = self.m_Tango.LSX_ConnectSimple(self.LSID, -1, "", 57600, 0)


            print("TANGO is now successfully connected to DLL")
            self.xpos,self.ypos=self.get_position()
            self.app.add_log("Tango connected")
            self.connected=True
        except:
            self.connected=False
            self.xpos,self.ypos=25,25
            self.app.add_log("Tango dummy mode")
            print("stage dummy mode")


        self.xlast=np.copy(self.xpos)
        self.ylast=np.copy(self.ypos)

        self.xpos_set=np.copy(self.xpos)
        self.ypos_set=np.copy(self.ypos)


        self.saved_positions=dict() 
        self.combolist=["choose position"]   
        self.textitems=[]
        self.symbolitems=[]

        self.xlimit=[0.,50.] # mm
        self.ylimit=[0.,50.] # mm 
        
        self.step_small_micron=10
        self.step_medium_micron=50
        self.step_large_micron=150

        self.step_size=self.step_medium_micron/1000 # mm
        

        self.cam_size=0.2


    def thread_task(self,event=None):
        self.worker=Status_update(self,event)
        self.worker.signals.string_update.connect(self.status_update_from_thread)
        self.app.threadpool.start(self.worker)


    def status_update_from_thread(self,string_x_y_tuple):
        self.app.status_stage.setText(string_x_y_tuple[0])
        self.xpos=string_x_y_tuple[1]
        self.ypos=string_x_y_tuple[2]
        self.plotactualpos.setData([self.xpos],[self.ypos])


        self.plot.removeItem(self.plotlast)
        xlow=self.xlast-self.cam_size/2
        xhigh=self.xlast+self.cam_size/2
        ylow=self.ylast-self.cam_size/2
        yhigh=self.ylast+self.cam_size/2
        cam_box_x=[xlow,xlow,xhigh,xhigh,xlow]
        cam_box_y=[ylow,yhigh,yhigh,ylow,ylow]

        self.plotlast=pg.PlotCurveItem(cam_box_x,cam_box_y)
        self.plot.addItem(self.plotlast)

        self.plot.removeItem(self.plotactualsquare)
        xlow=self.xpos-self.cam_size/2
        xhigh=self.xpos+self.cam_size/2
        ylow=self.ypos-self.cam_size/2
        yhigh=self.ypos+self.cam_size/2
        cam_box_x=[xlow,xlow,xhigh,xhigh,xlow]
        cam_box_y=[ylow,yhigh,yhigh,ylow,ylow]
        self.plotactualsquare=pg.PlotCurveItem(cam_box_x,cam_box_y, pen="#0fef1a")        
        self.plot.addItem(self.plotactualsquare)
        #self.plotactualsquare.setData([self.cam_box_x],[self.cam_box_y])
        

    def close(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()
            
        self.m_Tango.LSX_Disconnect(self.LSID)
        print("Tango disconnected")
    

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
        #else:
        #    print("Moved to " + str(X) + "," + str(Y) ) 
    
    def home_stage(self):
        self.app.add_log("Starting Homing Procedure ...")
        if self.live_mode_running:
            self.timer.stop()
        self.homeworker=Homing(self)
        self.homeworker.signals.string_update.connect(self.home_stage_done)
        self.app.threadpool.start(self.homeworker)

    def home_stage_done(self,string_x_y_tuple):
        if self.live_mode_running:
            self.timer.start(int(self.refresh_rate*1000))
        self.app.add_log("Finished Homing Procedure")
        self.status_update_from_thread(string_x_y_tuple)

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)


    def navigation_graphics_show(self,layout):
        self.plot = pg.PlotWidget()
        self.plot.setBackground(None)
        #self.plot.setXRange(-5,65)
        self.plot.setAspectLocked(True)

        self.plot.setLabel('bottom', 'x', units='mm')
        self.plot.setLabel('left', 'y', units='mm')
        self.plot.setTitle("Navigation")


        yvalues=[self.ylimit[0],self.ylimit[0],self.ylimit[1],self.ylimit[1],self.ylimit[0]]
        xvalues=[self.xlimit[0],self.xlimit[1],self.xlimit[1],self.xlimit[0],self.xlimit[0]]
        dashed_pen = pg.mkPen( width=2, style=pg.QtCore.Qt.DashLine)
        self.plot.plot([66],[52])
        self.plot.plot(xvalues,yvalues ,pen=dashed_pen)        
        
        xlow=self.xpos-self.cam_size/2
        xhigh=self.xpos+self.cam_size/2
        ylow=self.ypos-self.cam_size/2
        yhigh=self.ypos+self.cam_size/2
        cam_box_x=[xlow,xlow,xhigh,xhigh,xlow]
        cam_box_y=[ylow,yhigh,yhigh,ylow,ylow]

        self.plotlast=pg.PlotCurveItem(cam_box_x,cam_box_y)
        self.plot.addItem(self.plotlast)       
        self.plotactualsquare=pg.PlotCurveItem(cam_box_x,cam_box_y, pen="#0fef1a")
        self.plot.addItem(self.plotactualsquare)
        self.plotactualpos=pg.ScatterPlotItem([self.xpos],[self.ypos], pen="#0fef1a",symbol='x')
        self.plotactualpos.setSize(12)
        self.plot.addItem(self.plotactualpos)
        
        # 1D spectrum view end  ###################################################
        # Button overlayed inside the plot area
        bsize=30
        xshift=480
        self.btn_up = QPushButton("\u25B2", self.plot)
        self.btn_up.move(xshift, 0)  # position inside plot area
        self.btn_up.setStyleSheet("background-color: lightGray;font-size: 13pt")
        self.btn_up.setFixedSize(bsize,bsize)
        self.btn_up.clicked.connect(self.clicked_up)

        self.btn_down = QPushButton("\u25BC", self.plot)
        self.btn_down.move(xshift, 2*bsize)  # position inside plot area
        self.btn_down.setStyleSheet("background-color: lightGray;font-size: 13pt")
        self.btn_down.setFixedSize(bsize,bsize)
        self.btn_down.clicked.connect(self.clicked_down)

        self.btn_left = QPushButton("\u25C0", self.plot)
        self.btn_left.move(xshift-bsize, bsize)  # position inside plot area
        self.btn_left.setStyleSheet("background-color: lightGray;font-size: 19pt")
        self.btn_left.setFixedSize(bsize,bsize)
        self.btn_left.clicked.connect(self.clicked_left)

        self.btn_right = QPushButton("\u25B6", self.plot)
        self.btn_right.move(xshift+bsize, bsize)  # position inside plot area
        self.btn_right.setStyleSheet("background-color: lightGray;font-size: 19pt")
        self.btn_right.setFixedSize(bsize,bsize)
        self.btn_right.clicked.connect(self.clicked_right)

        self.btn_step = QPushButton("step size", self.plot)
        self.btn_step.move(xshift-bsize+10, int(3.5*bsize))  # position inside plot area
        self.btn_step.setStyleSheet("background-color: lightGray")#;font-size: 18pt")
        self.btn_step.setFixedWidth(70)
        self.btn_step.clicked.connect(self.set_step_size)

        self.btn_small = QPushButton("small", self.plot)
        self.btn_small.move(xshift-bsize+10, int(4.75*bsize))  # position inside plot area
        self.btn_small.setStyleSheet("background-color: cyan")#;font-size: 18pt")
        self.btn_small.setFixedWidth(70)
        self.btn_small.clicked.connect(self.clicked_small)

        self.btn_medium = QPushButton("medium", self.plot)
        self.btn_medium.move(xshift-bsize+10, int(6*bsize))  # position inside plot area
        self.btn_medium.setStyleSheet("background-color: lightGray")#;font-size: 18pt")
        self.btn_medium.setFixedWidth(70)
        self.btn_medium.clicked.connect(self.clicked_medium)

        self.btn_large = QPushButton("large", self.plot)
        self.btn_large.move(xshift-bsize+10, int(7.25*bsize))  # position inside plot area
        self.btn_large.setStyleSheet("background-color: orange")#;font-size: 18pt")
        self.btn_large.setFixedWidth(70)
        self.btn_large.clicked.connect(self.clicked_large)

        layout.addWidget(self.plot,2)

    def set_step_size(self):
        text="Set step widths of the navigation tool"
        labellist=["small (\u03BCm)","medium (\u03BCm)","large (\u03BCm)"]
        defaultlist=[self.step_small_micron,self.step_medium_micron,self.step_large_micron]
        self.window = self.app.entrymask3(self.app,"step_size",defaultlist,labellist,text)
        self.window.location_on_the_screen()
        self.window.show()

    def clicked_small(self):
        self.step_size=self.step_small_micron/1000
        self.btn_right.setStyleSheet("background-color: cyan;font-size: 19pt")
        self.btn_left.setStyleSheet("background-color: cyan;font-size: 19pt")
        self.btn_down.setStyleSheet("background-color: cyan;font-size: 13pt")
        self.btn_up.setStyleSheet("background-color: cyan;font-size: 13pt")


    def clicked_medium(self):
        self.step_size=self.step_medium_micron/1000
        self.btn_right.setStyleSheet("background-color: lightGray;font-size: 19pt")
        self.btn_left.setStyleSheet("background-color: lightGray;font-size: 19pt")
        self.btn_down.setStyleSheet("background-color: lightGray;font-size: 13pt")
        self.btn_up.setStyleSheet("background-color: lightGray;font-size: 13pt")


    def clicked_large(self):
        self.step_size=self.step_large_micron/1000
        self.btn_right.setStyleSheet("background-color: orange;font-size: 19pt")
        self.btn_left.setStyleSheet("background-color: orange;font-size: 19pt")
        self.btn_down.setStyleSheet("background-color: orange;font-size: 13pt")
        self.btn_up.setStyleSheet("background-color: orange;font-size: 13pt")

    def clicked_left(self):
        self.xpos_set=self.xpos-self.step_size
        self.stage_goto()

    def clicked_right(self):
        self.xpos_set=self.xpos+self.step_size
        self.stage_goto()

    def clicked_up(self):
        self.ypos_set=self.ypos+self.step_size
        self.stage_goto()

    def clicked_down(self):
        self.ypos_set=self.ypos-self.step_size
        self.stage_goto()


    def position_name_edited(self,s):
        if s:
            self.position_name=s

    def save_position(self):
        if self.position_name in self.saved_positions:
            self.app.add_log("Name already taken")
        else:   
            self.saved_positions[self.position_name]=(self.xpos,self.ypos)
            self.combolist.append(self.position_name)
            self.combowidget.addItem(self.position_name)
            
            self.textitems.append( pg.TextItem(self.position_name,color="white"))
            self.textitems[-1].setPos(self.xpos, self.ypos)
            self.plot.addItem(self.textitems[-1])

            self.symbolitems.append(pg.ScatterPlotItem([self.xpos],[self.ypos], pen="#ef0f2d",symbol='x'))
            self.symbolitems[-1].setSize(12)
            self.plot.addItem(self.symbolitems[-1])

            self.position_name="Position "+str(len(self.combolist))
            self.widgetsavpos.setText(self.position_name)


    def delete_position(self):
        if self.script_selected>0:
            del self.saved_positions[self.combolist[self.script_selected]]
            del self.combolist[self.script_selected]
            self.combowidget.removeItem(self.script_selected)
            self.plot.removeItem(self.textitems[self.script_selected])
            self.plot.removeItem(self.symbolitems[self.script_selected])
            del self.textitems[self.script_selected]
            del self.symbolitems[self.script_selected]
    
    def position_select_changed(self,i):
        self.script_selected=i
        if self.script_selected>0:
            x,y=self.saved_positions[self.combolist[self.script_selected]]
            self.widgetx.setText(str(x))
            self.stage_update_x(x)
            self.widgety.setText(str(y))
            self.stage_update_y(y)


    def stage_ui(self,layoutright):################################################################################
        self.refresh_rate=1.
        self.timer=QTimer()
        self.timer.timeout.connect(self.thread_task)
        self.live_mode_running=False



        self.expanded=False
        self.app.heading_label(layoutright,"Stage     ",self.expand)
    
        self.dropdown=QVBoxLayout()
        
        layoutstage=QHBoxLayout()

        self.widgetx = QLineEdit()
        self.widgetx.setStyleSheet("background-color: lightGray")
        self.widgetx.setMaxLength(7)
        self.widgetx.setFixedWidth(self.app.standard_width)
        self.widgetx.setText(str(self.xpos_set))
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
        self.widgety.setText(str(self.ypos_set))
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

        self.app.normal_button(layoutstagebuttons,"Home",self.home_stage)

        self.dropdown.addLayout(layoutstagebuttons)

        layoutsavpos=QHBoxLayout()

        self.widgetsavpos = QLineEdit()
        self.widgetsavpos.setStyleSheet("background-color: lightGray")
        self.widgetsavpos.setMaxLength(15)
        self.widgetsavpos.setFixedWidth(160)
        self.position_name="Position "+str(len(self.combolist))
        self.widgetsavpos.setText(self.position_name)
        self.widgetsavpos.textEdited.connect(self.position_name_edited)
        layoutsavpos.addWidget(self.widgetsavpos)
        
        layoutsavpos.addStretch()
        btn=self.app.normal_button(layoutsavpos,"Save Position",self.save_position)        
        btn.setFixedWidth(110)

        
        self.dropdown.addLayout(layoutsavpos)


        layoutchoosepos=QHBoxLayout()
        self.combowidget = QComboBox()
        self.script_selected=0
        self.combowidget.addItems(self.combolist)
        self.combowidget.setStyleSheet("background-color: lightGray")
        self.combowidget.setFixedHeight(25)
        self.combowidget.setFixedWidth(160)
        self.combowidget.currentIndexChanged.connect(self.position_select_changed ) 

        layoutchoosepos.addWidget(self.combowidget)

        layoutchoosepos.addStretch()
        btn=self.app.normal_button(layoutchoosepos,"Delete Position",self.delete_position) 
        btn.setFixedWidth(110)

        
        self.dropdown.addLayout(layoutchoosepos)


        layoutstagebuttons2=QHBoxLayout()
        
        
        btn=self.app.normal_button(layoutstagebuttons2,"Set Limits",self.entry_window_limits)  
        btn.setFixedWidth(110)
        layoutstagebuttons2.addStretch()
        #btn=self.app.normal_button(layoutstagebuttons2,"Calibrate Spatial Cam",self.calibrate_spatial_cam)  
        #btn.setStyleSheet("background-color: dimgrey")
        #btn.setFixedWidth(130)

        #layoutstagebuttons3=QHBoxLayout()
        #self.btnlive=self.app.normal_button(layoutstagebuttons3,"Status Live",self.live_mode)

        self.dropdown.addLayout(layoutstagebuttons2)
        #self.dropdown.addLayout(layoutstagebuttons3)

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)

        layoutright.addItem(self.app.vspace)

        if self.connected:
            self.live_mode()

    #def calibrate_spatial_cam(self):
    #    pass


    def live_mode(self):
        if not self.live_mode_running:
            self.live_mode_running=True
            self.timer.start(int(self.refresh_rate)*1000)
            #self.btnlive.setStyleSheet("background-color: green;color: black")
        else:

            self.live_mode_running=False
            self.timer.stop()
            #self.btnlive.setStyleSheet("background-color: lightGray;color: black")


    # stage ui  methods ##########################################################
    def entry_window_limits(self):
        text="Stage safety limits (position in mm)"
        labellist=["X min","Y min","X max","Y max"]
        defaultlist=[self.xlimit[0],self.ylimit[0],self.xlimit[1],self.ylimit[1]]
        self.w = self.app.entrymask4(self.app,"stage_limits",defaultlist,labellist,text)
        self.w.location_on_the_screen()
        self.w.show()
        
    def stage_actual(self):
        if self.live_mode_running:
            self.timer.stop()
            self.xpos,self.ypos=self.get_position()
            self.xpos_set=np.copy(self.xpos)
            self.ypos_set=np.copy(self.ypos)
            self.timer.start(int(self.refresh_rate*1000))
        else:
            self.xpos,self.ypos=self.get_position()
            self.xpos_set=np.copy(self.xpos)
            self.ypos_set=np.copy(self.ypos)
            
        self.widgety.setText(str(self.ypos_set))
        self.widgetx.setText(str(self.xpos_set))
        self.widgetx.setStyleSheet("background-color: lightGray;color: black")
        self.widgety.setStyleSheet("background-color: lightGray;color: black")

        
    def stage_goto(self):
        cond1=self.xpos > self.xlimit[0]
        cond2=self.xpos < self.xlimit[1]
        cond3=self.ypos > self.ylimit[0]
        cond4=self.ypos < self.ylimit[1]

        if cond1*cond2*cond3*cond4:        
                
            if self.live_mode_running:
                self.timer.stop()
            self.xlast,self.ylast=self.get_position()
            self.set_position(self.xpos_set,self.ypos_set)
            self.xpos,self.ypos=self.get_position()
            self.widgety.setText(str(self.ypos))
            self.widgetx.setText(str(self.xpos))
            self.widgetx.setStyleSheet("background-color: lightGray;color: black")
            self.widgety.setStyleSheet("background-color: lightGray;color: black")

            if self.live_mode_running:
                self.timer.start(int(self.refresh_rate*1000))
            
            self.app.add_log("x=" + str(self.xpos) + " mm, y=" + str(self.ypos)+" mm" )
            self.app.add_log("Stage moved to:") 
        else:
            self.app.add_log("point outside stage limits")
            self.app.add_log("move aborted")
        
    def stage_update_x(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.xpos_set=np.double(s)
                self.widgetx.setStyleSheet("background-color: lightGray;color: red")

    def stage_update_y(self,s):
        if s:
            try:
               itsanumber=np.double(s)
               itsanumber=True
            except:
                itsanumber=False
            if itsanumber:
                self.ypos_set=np.double(s)
                self.widgety.setStyleSheet("background-color: lightGray;color: red")


    #def refreshrate_edited(self,s):
    #    if s:
    #        if self.live_mode_running:
    #            self.refresh_rate=np.double(s)
    #            self.timer.stop()
    #            self.timer.start(int(1000*self.refresh_rate))
    #        else:
    #            self.refresh_rate=np.double(s)

"""

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


    def home_all(self):
        self.app.add_log("Starting Homing Procedure ...")
        QApplication.processEvents()
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

        self.stage_actual()
        self.app.add_log("Finished Homing Procedure")

        #print("stage homed")

"""