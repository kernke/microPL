# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSize,QTimer,QThread, QObject, pyqtSignal, pyqtSlot,QThreadPool,QRunnable#,QChecked
#from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget,QFileDialog,QLabel,QGridLayout,QComboBox,QDesktopWidget,QDialog,QApplication,QCheckBox


import pyqtgraph as pg
import numpy as np
import h5py
import datetime
import os

import sys
# caution: path[0] is reserved for script path (or '' in REPL)
sys.path.insert(1, r'C:\Users\user\Documents\Python\MicroPL_package\MicroPL\Pixis')
from cam import Pixis
sys.path.insert(1, r'C:\Users\user\Documents\Python\MicroPL_package\MicroPL\stage_scripts')
from stage import Stage
sys.path.insert(1, r'C:\Users\user\Documents\Python\MicroPL_package\MicroPL\SCT320_Wrapper')
from mono import SCT320
sys.path.insert(1, r'C:\Users\user\Documents\Python\MicroPL_package\MicroPL\Hamamatsu')
from orca import Orca


#color_text_on_dark="white"
#color_text_on_bright="black"
#color_interactive_stuff="lightGray"
#color_background="black"

def heading_label(layout,heading_string):
    label = QLabel(heading_string)
    label.setStyleSheet("color:white;font-size: 11pt")
    layout.addWidget(label)
    
def normal_button(layout,text,function):
    button = QPushButton(text)
    button.setStyleSheet("background-color: lightGray")
    button.clicked.connect(function)
    layout.addWidget(button)
    return button


class CameraSignals(QObject):

    camsignal = pyqtSignal(object)   

class CameraHandler(QRunnable):

    def __init__(self, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.args = args
        self.kwargs = kwargs
        self.signals = CameraSignals()

        # Add the callback to our kwargs
        #self.kwargs['progress_callback'] = self.signals.progress

    
    @pyqtSlot()
    def run(self): # A slot takes no params
        cimg=device.pixis.acquire(device.acqtime,0, 1024, 0, 256, 1,1,show=False)
        print("max intens: "+str(np.max(cimg)))
        self.signals.camsignal.emit(cimg)
        

class saving:
    def __init__(self):
        self.acq_number=0
        self.defaultname="acq_"
        self.defaultgroup="measurement"
        self.default_file_name=r'microPL_'
        self.h5struc=self.defaultgroup+"/"+self.defaultname+str(self.acq_number).zfill(3)
        self.default_folder=r"C:\Users\user\Documents\Data\test"
        allfiles=os.listdir(self.default_folder)
        filenumbers=[-1]
        for i in allfiles:
            if "microPL_" == i[:8]:
                if i[8:-3].isnumeric():
                    filenumbers.append(int(i[8:-3]))
        newnumber=int(np.max(filenumbers)+1)
        self.default_file_name+=str(newnumber)        
        self.filepath=os.path.join(self.default_folder, self.default_file_name+".h5")

    def write_to_h5(self,data,app):
        with h5py.File(self.filepath, 'a') as hf:
            hf[self.h5struc+"/wavelengths"]=data[0]
            hf[self.h5struc+"/spectrum"]=data[1]
            if app.save_full_image:
                hf[self.h5struc+"/image"]=data[2]
            for i in data[3]:
                hf[self.h5struc+"/"+i]=data[3][i]
            
        self.acq_number+=1
        self.h5struc=self.defaultgroup+"/"+self.defaultname+str(self.acq_number).zfill(3)
        app.widgeth5.setText(self.h5struc)
        print("saved")

    def check_h5(self,app):
        check=True
        with h5py.File(self.filepath, 'a') as hf:    
            if self.h5struc in hf:
                app.save_warning()
                check=False
        return check

class device_interface:
    def __init__(self):
        self.acqtime=1

        self.connect_all()
        self.xlimit=[0.,50.]
        self.ylimit=[0.,50.]
        self.xpos,self.ypos=self.stage.get_position()
        
        # monochromator
        self.wavelength=self.monochromator.get_wavelength()

        self.grating_idx,self.densities,self.blazes=self.monochromator.gratings()
        self.grating_list=[]
        self.grating_pos=self.monochromator.get_grating()[0]
        for i in range(len(self.grating_idx)):
            s=str(self.grating_idx[i])
            s+=" - density : "+str(self.densities[i])
            s+=" - blaze : "+str(self.blazes[i])
            self.grating_list.append(s)
        self.grating_actual=self.grating_list[int(self.grating_pos-1)]
        
        # check if -1 is needed, check unit of densities
        self.spectrum_x_axis= self.grating_wavelength(self.densities[int(self.grating_pos-1)],self.wavelength) #Wavelength array

        # stage mapping
        self.script_x_entries=None
        self.script_y_entries=None
        self.script_execution=False
        self.script_index=None

    def grating_wavelength(self,d_mm, lamda_nm, f_mm = 327, x_microns = 26.0, delta = 0,m = 1):
        """
        Computes the modified wavelength based on input parameters.
        Parameters:
        - f: focal length
        - x: CCD width/mm
        - delta: rotation angle (radians)
        - d: distance between grooves (mm)
        - m: diffractive order, here m = 1  

        """
        # Conversions
        d_mm = 1 / d_mm 
        lamda_mm = lamda_nm / 1E6
        x_mm = x_microns / 1E3
        # Compute psi (grating angle)
        gamma = 0.310737  # radians
        psi = np.arcsin((m * lamda_mm) / (2 * d_mm  * np.cos(gamma / 2)) )
        # Compute ksi angle
        indices = np.arange(-511.5, 512, 1)
        xi = np.arctan((x_mm * indices * np.cos(delta)) / (f_mm + indices * x_mm * np.sin(delta)))
        # Step 3: Compute new wavelength using psi and epsilon
        new_lamda = (d_mm / m) * (np.sin(psi - gamma / 2) + np.sin(psi + gamma / 2 + xi))
        new_lamda=new_lamda*1E6
        return new_lamda[::-1]


    def connect_all(self):
        self.pixis = Pixis()
        self.stage = Stage()
        self.monochromator = SCT320()
        self.connected=True
        
    def disconnect_all(self):
        self.pixis.close()
        self.stage.close()
        self.monochromator.disconnect()
        self.connected=False


class WarnWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warning")
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


class EntryMask4(QWidget):
    def __init__(self,check_bool):
        super().__init__()
        self.setWindowTitle("Enter Values")
        self.setStyleSheet("background-color: black;") 
        self.setFixedSize(QSize(300, 200))
        if check_bool:
            self.tempo_xmin=int(roi.pos()[0])
            self.tempo_ymin=int(roi.pos()[1])
            self.tempo_xmax=int(roi.pos()[0]+roi.size()[0])
            self.tempo_ymax=int(roi.pos()[1]+roi.size()[1])
        else:
            self.tempo_xmin=device.xlimit[0]
            self.tempo_ymin=device.ylimit[0]
            self.tempo_xmax=device.xlimit[1]
            self.tempo_ymax=device.ylimit[1]
    

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

        normal_button(layout,"Confirm",lambda: self.confirm_and_close(check_bool))

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
            roi.setPos(pg.Point([self.tempo_xmin,self.tempo_ymin]))
            deltax=self.tempo_xmax-self.tempo_xmin
            deltay=self.tempo_ymax-self.tempo_ymin
            roi.setSize([deltax,deltay])
        else: #stage
            device.xlimit=[self.tempo_xmin,self.tempo_xmax]
            device.ylimit=[self.tempo_ymin,self.tempo_ymax]
            
        self.close()


class EntryMask6(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Values")
        self.setStyleSheet("background-color: black;") 
        self.setFixedSize(QSize(350, 300))

        if device.script_x_entries is None:
            self.tempo_xmin=0.
            self.tempo_ymin=0.
            self.tempo_xmax=50.
            self.tempo_ymax=50.
            self.tempo_xnum=10
            self.tempo_ynum=10
            device.script_x_entries=[self.tempo_xmin,self.tempo_xmax,int(self.tempo_xnum)]
            device.script_y_entries=[self.tempo_ymin,self.tempo_ymax,int(self.tempo_ynum)]
        else:
            self.tempo_xmin=device.script_x_entries[0]
            self.tempo_ymin=device.script_y_entries[0]
            self.tempo_xmax=device.script_x_entries[1]
            self.tempo_ymax=device.script_y_entries[1]
            self.tempo_xnum=device.script_x_entries[2]
            self.tempo_ynum=device.script_y_entries[2]
        

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
            device.script_x_entries[0]=self.tempo_xmin
        
    def temporary_ymin(self,s):
        if s:
            self.tempo_ymin=np.double(s)
            device.script_y_entries[0]=self.tempo_ymin

    def temporary_xmax(self,s):
        if s:
            self.tempo_xmax=np.double(s)
            device.script_x_entries[1]=self.tempo_xmax

    def temporary_ymax(self,s):
        if s:
            self.tempo_ymax=np.double(s)
            device.script_y_entries[1]=self.tempo_ymax

    def temporary_xnum(self,s):
        if s:
            self.tempo_xnum=int(s)
            device.script_x_entries[2]=self.tempo_xnum

    def temporary_ynum(self,s):
        if s:
            self.tempo_ynum=int(s)
            device.script_y_entries[2]=self.tempo_ynum

            
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
        
        device.script_positions_x=newx
        device.script_positions_y=newy  
        device.script_execution=True
        self.close()

          
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        global roi,roiplot,device,h5saving,metadata
        self.setWindowTitle("MicroPL App")
        self.setStyleSheet("background-color: black;")#black 
        self.move(400,200)
        self.save_on_acquire_bool=False
        self.save_full_image=True
        self.live_mode_running=False

        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)
        
        h5saving=saving()
        device=device_interface()
        
        cimg=np.zeros([256,1024])
        metadata=dict()
        
        layoutmain = QHBoxLayout() # whole window
        layoutright = QVBoxLayout() # right side containing image,colorbar and 1D-roi-plot
        layoutleft = QVBoxLayout() # left side containing all the buttons

        # image view window start########################################################
        cw = QWidget() 
        layout = QGridLayout()
        cw.setLayout(layout)
        layout.setSpacing(0)
        view = pg.GraphicsView()
        vb = pg.ViewBox()
        vb.setAspectLocked()
        view.setCentralItem(vb)
        layout.addWidget(view, 0, 0, 4, 1)

        self.img=pg.ImageItem()
        self.img.setImage(cimg.T)
        vb.addItem(self.img)
        vb.invertY(True)
        vb.autoRange()
        
        hist = pg.HistogramLUTWidget(gradientPosition="left")
        hist.setLevelMode(mode="mono")
        layout.addWidget(hist, 0, 1)
        hist.setImageItem(self.img)

        # ROI
        roi=pg.RectROI([0, 100], [1024, 20], pen=(0,9))
        vb.addItem(roi)
        
        # image view window end########################################################
        layoutleft.addWidget(cw)    
        # 1D spectrum view start ###################################################
        roiplot = pg.PlotWidget()
        roiplot.setFixedHeight(300)
        roi.sigRegionChanged.connect(self.updateRoi)
        data = roi.getArrayRegion(self.img.image, img=self.img)
        
        #xvalues=np.arange(data.shape[0])
        yvalues=data.mean(axis=-1)
        roi.curve=roiplot.plot(device.spectrum_x_axis,yvalues )        
        # 1D spectrum view end  ###################################################
        layoutleft.addWidget(roiplot)
    
        layoutmain.addLayout( layoutleft )

        # user interface buttons start ###############################################
        ui= QWidget() 
        ui.setFixedWidth(250)
        ui.setLayout(layoutright)
        
        heading_label(layoutright,"Camera")######################################################

        layoutacqtime=QHBoxLayout()
        widget = QLineEdit()
        widget.setStyleSheet("background-color: lightGray")
        widget.setMaxLength(7)
        widget.setFixedWidth(60)
        widget.setText(str(device.acqtime))
        layoutacqtime.addWidget(widget)
        widget.textEdited.connect(self.acqtime_edited)

        label = QLabel("acquisition time [ s ]")
        label.setStyleSheet("color:white")
        layoutacqtime.addWidget(label)

        layoutright.addLayout(layoutacqtime)

        layoutacqbutton=QHBoxLayout()
        self.btnacq = normal_button(layoutacqbutton,"Acquire",self.acquire_clicked)
        self.btnacq.setFixedWidth(60)
        layoutacqbutton.addStretch()

        self.timer=QTimer()
        self.timer.timeout.connect(self.acquire_clicked)
        
        self.btnlive = normal_button(layoutacqbutton,"Live",self.live_mode)
        self.btnlive.setFixedWidth(60)
        
        layoutacqbutton.addStretch()

        btn=normal_button(layoutacqbutton,"set ROI",self.entry_window_roi)
        btn.setFixedWidth(60)

        layoutright.addLayout(layoutacqbutton)
        layoutright.addStretch()
        
        heading_label(layoutright,"Stage")####################################################
    
        layoutstagebuttons=QHBoxLayout()
        btn=normal_button(layoutstagebuttons,"GoTo",self.stage_goto)
        btn.setFixedWidth(80)

        layoutstagebuttons.addStretch()

        btn=normal_button(layoutstagebuttons,"Actual",self.stage_actual)        
        btn.setFixedWidth(80)

        layoutright.addLayout(layoutstagebuttons)
        
        layoutstage=QHBoxLayout()

        self.widgetx = QLineEdit()
        self.widgetx.setStyleSheet("background-color: lightGray")
        self.widgetx.setMaxLength(7)
        self.widgetx.setFixedWidth(60)
        self.widgetx.setText(str(device.xpos))
        self.widgetx.textEdited.connect(self.stage_update_x)
        layoutstage.addWidget(self.widgetx)
        
        label = QLabel("X (mm)")
        label.setStyleSheet("color:white")
        layoutstage.addWidget(label)
        
        horizontalspace = QLabel("---")
        layoutstage.addWidget(horizontalspace)

        self.widgety = QLineEdit()
        self.widgety.setStyleSheet("background-color: lightGray")
        self.widgety.setMaxLength(7)
        self.widgety.setFixedWidth(60)
        self.widgety.setText(str(device.ypos))
        self.widgety.textEdited.connect(self.stage_update_y)
        layoutstage.addWidget(self.widgety)       
        
        label = QLabel("Y (mm)")
        label.setStyleSheet("color:white")
        layoutstage.addWidget(label)
        
        layoutright.addLayout(layoutstage)

        layoutstagebuttons2=QHBoxLayout()
        btn=normal_button(layoutstagebuttons2,"Home",self.stage_home)
        btn.setFixedWidth(80)

        layoutstagebuttons2.addStretch()

        btn=normal_button(layoutstagebuttons2,"Limits",self.entry_window_limits)        
        btn.setFixedWidth(80)

        layoutright.addLayout(layoutstagebuttons2)
        layoutright.addStretch()

        heading_label(layoutright,"Monochromator")###########################################
        
        layoutwavelength=QHBoxLayout()
        self.widgetwave = QLineEdit()
        self.widgetwave.setStyleSheet("background-color: lightGray")
        self.widgetwave.setMaxLength(7)
        self.widgetwave.setFixedWidth(60)
        self.widgetwave.setText(str(device.wavelength))
        self.widgetwave.textEdited.connect(self.wavelength_updated)
        self.widgetwave.returnPressed.connect(self.wavelength_edited)
        layoutwavelength.addWidget(self.widgetwave)

        label = QLabel("wavelength [ nm ]\n(confirm with enter)")
        label.setWordWrap(True) 
        label.setStyleSheet("color:white")
        layoutwavelength.addWidget(label)
        layoutright.addLayout(layoutwavelength)
        
        layoutgrating=QHBoxLayout()
        widget = QComboBox()
        widget.addItems(device.grating_list)
        widget.setStyleSheet("background-color: lightGray")
        widget.setFixedHeight(25)
        widget.setCurrentIndex(int(device.grating_pos-1))
        widget.currentIndexChanged.connect(self.grating_changed )
        layoutgrating.addWidget(widget)

        
        label = QLabel("grating")
        label.setStyleSheet("color:white")
        layoutgrating.addWidget(label)

        layoutright.addLayout(layoutgrating)
        layoutright.addStretch()
  
        heading_label(layoutright,"Saving")#################################################
        
        self.checkbox = QCheckBox('save full chip image', self)
        self.checkbox.setStyleSheet("color:white")
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(self.checkbox_full_saving)
        layoutright.addWidget(self.checkbox)
        
        layoutsavetext=QHBoxLayout()
        labelsave = QPushButton()
        labelsave.setStyleSheet("background-color: lightGray; text-align: left")
        labelsave.setText("..."+h5saving.filepath[-32:])
        labelsave.clicked.connect(self.set_filepath)
        self.labelsave=labelsave
        layoutsavetext.addWidget(labelsave)

        label = QLabel("file")
        label.setStyleSheet("color:white")
        layoutsavetext.addWidget(label)
        layoutright.addLayout(layoutsavetext)

        layoutsaveh5=QHBoxLayout()
        self.widgeth5 = QLineEdit()
        self.widgeth5.setStyleSheet("background-color: lightGray")
        self.widgeth5.setText(h5saving.h5struc)
        layoutsaveh5.addWidget(self.widgeth5)
        self.widgeth5.textEdited.connect(self.h5struc_edited)

        label = QLabel("h5")
        label.setStyleSheet("color:white")
        layoutsaveh5.addWidget(label)
        layoutright.addLayout(layoutsaveh5)

        layoutsavebuttons=QHBoxLayout()
        self.btnsave = QPushButton("Save")
        self.btnsave.setStyleSheet("background-color: lightGray")
        self.btnsave.clicked.connect(self.save_to_h5)
        self.btnsave.setFixedWidth(80)

        layoutsavebuttons.addWidget(self.btnsave)
        layoutsavebuttons.addStretch()

        self.btnsaveacq=normal_button(layoutsavebuttons,"Save on Acquire",self.save_on_acquire)
        self.btnsaveacq.setFixedWidth(100)
    
        layoutright.addLayout(layoutsavebuttons)    
        layoutright.addStretch()

        labelbox=QHBoxLayout()
        heading_label(labelbox,"Scripts") #################################################
        labelbox.addStretch()

        self.labelscr = QLabel("")
        self.labelscr.setStyleSheet("color:white")
        self.labelscr.setFixedWidth(100)
        labelbox.addWidget(self.labelscr)
        
        layoutright.addLayout(labelbox)
        
        widget = QComboBox()
        self.script_selected=0
        widget.addItems(["","from settings txt","grid mapping"])
        widget.setStyleSheet("background-color: lightGray")
        widget.setFixedHeight(25)
        widget.currentIndexChanged.connect(self.script_changed )        
        layoutright.addWidget(widget)

        layoutscriptbuttons=QHBoxLayout()

        self.btnexec = normal_button(layoutscriptbuttons,"Execute",self.script_button_execute)
        self.btnexec.setFixedWidth(60)

        layoutscriptbuttons.addStretch()
        label = QLabel("click only once\n(wait one acq-time)")
        label.setStyleSheet("color:white")
        label.setWordWrap(True)
        layoutscriptbuttons.addWidget(label)
        
        self.btnpause = normal_button(layoutscriptbuttons,"Pause",self.script_button_pause)
        self.btnpause.setFixedWidth(60)
        
        layoutright.addLayout(layoutscriptbuttons)
        # user interface buttons end ###############################################
        
        layoutmain.addWidget(ui)
        widget = QWidget()
        widget.setLayout(layoutmain) 
        self.setCentralWidget(widget)


    def closeEvent(self, event):
        if device.connected:
            device.disconnect_all()
            
        can_exit=True
        if can_exit:
            event.accept() # let the window close
        else:
            event.ignore()


            
    def script_button_pause(self):
        if device.script_execution:
            self.btnpause.setText("Continue")
            device.script_execution=False
        else:
            self.btnpause.setText("Pause")
            device.script_execution=True
            if self.script_selected==1:
                self.script_from_txt()
            elif self.script_selected==2:
                self.entry_window_script_grid()

    def script_end(self):
        device.script_execution=False
        device.script_index=None
        self.save_on_acquire()
        self.btnexec.setText("Execute")
        self.labelscr.setText("")
    
    def script_button_execute(self):
        if self.script_selected==0:
            print("no script selected to execute")
            
        elif self.script_selected==1:
            if device.script_execution==False and device.script_index is None:
                self.script_from_txt()
            else:
                self.script_end()

        elif self.script_selected==2:
            if device.script_execution==False and device.script_index is None:
                self.entry_window_script_grid()
            else:
                self.script_end()


    
    def script_from_txt(self):
        fname,ftype = QFileDialog.getOpenFileName(self, 'Open file', 
               h5saving.default_folder,"settings list (*.txt)")
        #print(fname)
        if fname:
            settings_array=np.genfromtxt(fname,delimiter=",",skip_header=1)
            #print(settings_array)

            device.script_execution=True
            if device.script_index is None:
                device.script_index=0
            self.btnexec.setText("Cancel")
                
            if not self.save_on_acquire_bool:
                self.save_on_acquire()
            
            
            number_of_points=len(settings_array)        
            for i in range(device.script_index,number_of_points):
                device.acqtime=settings_array[i,0]
            
                device.wavelength=settings_array[i,1]
                self.wavelength_edited()

                self.grating_changed(int(settings_array[i,2]-1))
                
                device.xpos=settings_array[i,3]
                device.ypos=settings_array[i,4]
                self.stage_goto()

                self.save_full_image=bool(settings_array[i,5])
                self.checkbox.setChecked(self.save_full_image)
                QApplication.processEvents()
                if device.script_execution==False:
                    return None                
                self.acquire_clicked()
                device.script_index+=1
                print(str(i+1)+" from "+str(number_of_points))
                self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                QApplication.processEvents()
                if device.script_execution==False:
                    return None
                    
            self.script_end()

            
    def script_changed(self,i):
        self.script_selected=i

            
    def entry_window_script_grid(self):
        if device.script_index is None:
            self.w = EntryMask6()
            self.w.location_on_the_screen()
            self.w.exec()

        # execute script
        if device.script_execution:
            if device.script_index is None:
                device.script_index=0
            self.btnexec.setText("Cancel")
            if not self.save_on_acquire_bool:
                self.save_on_acquire()
            number_of_points=len(device.script_positions_x)        
            for i in range(device.script_index,number_of_points):
                device.xpos=device.script_positions_x[i]
                device.ypos=device.script_positions_y[i]
                self.stage_goto()      
                xcheck,ycheck=device.stage.get_position()
                print("check position: "+str(xcheck)+","+str(ycheck))
                
                QApplication.processEvents()
                if device.script_execution==False:
                    return None
                self.acquire_clicked()
                device.script_index+=1
                print(str(i+1)+" from "+str(number_of_points))
                self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                QApplication.processEvents()
                if device.script_execution==False:
                    return None
                    
            self.script_end()
            
    
    # monochromator methods #############################################
    def wavelength_updated(self,s):
        if s:
            device.wavelength=np.double(s)
            self.widgetwave.setStyleSheet("background-color: lightGray;color: red")
    
    def wavelength_edited(self):
        device.monochromator.set_wavelength(device.wavelength)
        device.wavelength=device.monochromator.get_wavelength()
        device.spectrum_x_axis= device.grating_wavelength(device.densities[int(device.grating_pos-1)],device.wavelength)
        self.widgetwave.setText(str(device.wavelength))
        self.widgetwave.setStyleSheet("background-color: lightGray;color: black")

    def grating_changed(self, i): # i is an int
        device.monochromator.set_grating(int(i+1))
        device.grating_pos=device.monochromator.get_grating()[0]    
        device.spectrum_x_axis= device.grating_wavelength(device.densities[int(device.grating_pos-1)],device.wavelength)
        device.grating_actual=device.grating_list[int(device.grating_pos-1)]
        
        
    # saving methods ######################################################
    def checkbox_full_saving(self,state):
        if state == 2:
            print("Full image saving enabled")
            self.save_full_image=True
        else:
            self.save_full_image=False
            print("Full image saving disabled")
    
    def save_on_acquire(self):
        self.save_on_acquire_bool=not self.save_on_acquire_bool
        if self.save_on_acquire_bool:
            self.btnacq.setStyleSheet("background-color: green")
            self.btnsaveacq.setStyleSheet("background-color: green")
            self.btnsave.setStyleSheet("background-color: red")
        else:
            self.btnacq.setStyleSheet("background-color: lightGray")
            self.btnsaveacq.setStyleSheet("background-color: lightGray")
            self.btnsave.setStyleSheet("background-color: lightGray")

            
    def save_to_h5(self):
        if h5saving.check_h5(self):
            profile = roi.getArrayRegion(self.img.image, img=self.img)
            spec_y=profile.mean(axis=-1)
            spec_x=device.spectrum_x_axis#np.arange(len(spec_y))
            
            data=[spec_x,spec_y,self.img.image,metadata]
            h5saving.write_to_h5(data,self)

    def h5struc_edited(self,s):
        if s:
            index=s.find("/")
            h5saving.defaultgroup=s[:index]
            h5saving.h5struc=s
    
    def save_warning(self):
        self.w = WarnWindow()
        self.w.setWarnText("This h5-path already exists")
        self.w.location_on_the_screen()
        self.w.show()
     
    def set_filepath(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save spectrum", h5saving.filepath, "spectra (*.h5)",
            options=QFileDialog.DontConfirmOverwrite
        )
        if filename:
            h5saving.filepath=filename
            self.labelsave.setText("..."+h5saving.filepath[-32:])

    # stage methods ##########################################################
    def entry_window_limits(self):
        self.w = EntryMask4(False)
        self.w.setHeading("Stage safety limits (position in mm)")
        self.w.location_on_the_screen()
        self.w.show()
        
    def stage_actual(self):
        device.xpos,device.ypos=device.stage.get_position()
        self.widgety.setText(str(device.ypos))
        self.widgetx.setText(str(device.xpos))
        self.widgetx.setStyleSheet("background-color: lightGray;color: black")
        self.widgety.setStyleSheet("background-color: lightGray;color: black")

        
    def stage_goto(self):
        cond1=device.xpos > device.xlimit[0]
        cond2=device.xpos < device.xlimit[1]
        cond3=device.ypos > device.ylimit[0]
        cond4=device.ypos < device.ylimit[1]

        if cond1*cond2*cond3*cond4:        
            device.stage.set_position(device.xpos,device.ypos)    
            self.stage_actual()
            print("arrived")
        else:
            print("move aborted")
            print("point outside stage limits")
        
    def stage_update_x(self,s):
        if s:
            device.xpos=np.double(s)
            self.widgetx.setStyleSheet("background-color: lightGray;color: red")

    def stage_update_y(self,s):
        if s:
            device.ypos=np.double(s)
            self.widgety.setStyleSheet("background-color: lightGray;color: red")

    def stage_home(self):
        device.stage.home_all()    
        self.stage_actual()
        print("stage homed")

    # acquistion methods #######################################################
    def live_mode(self):
        if self.live_mode_running:
            self.live_mode_running=False
            self.timer.stop()
            self.btnlive.setText("Live")
            self.btnlive.setStyleSheet("background-color: lightGray;color: black")
        else:
            self.live_mode_running=True
            self.timer.start(device.acqtime*1000)
            self.btnlive.setText("stop")
            self.btnlive.setStyleSheet("background-color: green;color: black")
    
    def acqtime_edited(self,s):
        if s:
            device.acqtime=np.double(s)
            if self.live_mode_running and device.acqtime>0.0001:
                self.timer.stop()
                self.timer.start(device.acqtime*1000+1000)

    def updateRoi(self):
        if roi is None:
            return
        data = roi.getArrayRegion(self.img.image, img=self.img)
        roi.curve.setData(device.spectrum_x_axis, data.mean(axis=-1))#np.arange(data.shape[0])

    def entry_window_roi(self):
        self.w = EntryMask4(True)
        self.w.setHeading("ROI in Pixels with chip dimension 1024x256\nY increases from top to bottom\n(entries must be integers)")
        self.w.location_on_the_screen()
        self.w.show()  

    def acquire_clicked(self):
        self.camera_handler =CameraHandler() 
        self.camera_handler.signals.camsignal.connect(self.image_from_thread)
        self.threadpool.start(self.camera_handler)
        #self.cam_thread.start()
        #cimg=device.pixis.acquire(device.acqtime,0, 1024, 0, 256, 1,1,show=False)
        #print("max intens: "+str(np.max(cimg)))
        metadata["ROI_origin"]=(roi.pos()[0],roi.pos()[1])
        metadata["ROI_extent"]=(roi.size()[0],roi.size()[1])
        metadata["time_stamp"]=datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S.%f")
        metadata["acquisition_time"]=device.acqtime
        metadata["center_wavelength"]=device.wavelength
        xacq,yacq=device.stage.get_position()
        metadata["x"]=xacq
        metadata["y"]=yacq
        metadata["grating"]=device.grating_actual
        #self.img.setImage(cimg.T)
        #self.updateRoi()
        #if self.save_on_acquire_bool:
        #    self.save_to_h5()

    def image_from_thread(self,cimg):
        self.img.setImage(cimg.T)
        self.updateRoi()
        if self.save_on_acquire_bool:
            self.save_to_h5()
        