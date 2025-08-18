from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QWidget,QFileDialog,QLabel,QGridLayout,QComboBox,QApplication,QCheckBox
from PyQt5.QtCore import QTimer
import numpy as np

class Scripting:
    def __init__(self,app):
        self.app=app
        
        # stage mapping
        self.script_x_entries=None
        self.script_y_entries=None
        self.script_execution=False
        self.script_index=None



    def script_ui(self,layoutright):

        #labelbox=QHBoxLayout()
        self.app.heading_label(layoutright,"Scripts") #################################################
        #labelbox.addStretch()

        self.labelscr = QLabel("")
        self.labelscr.setStyleSheet("color:white")
        self.labelscr.setFixedWidth(100)
        #labelbox.addWidget(self.labelscr)
        
        #layoutright.addLayout(labelbox)
        
        widget = QComboBox()
        self.script_selected=0
        widget.addItems(["","from settings txt","grid mapping spatial","grid mapping spectral","grid mapping both"])
        widget.setStyleSheet("background-color: lightGray")
        widget.setFixedHeight(25)
        widget.currentIndexChanged.connect(self.script_changed )        
        layoutright.addWidget(widget)

        layoutscriptbuttons=QHBoxLayout()

        self.btnexec = self.app.normal_button(layoutscriptbuttons,"Execute",self.script_button_execute)
        #self.btnexec.set

        layoutscriptbuttons.addStretch()
        label = QLabel("click only once ->\n(wait one acq-time)")
        label.setStyleSheet("color:white")
        label.setWordWrap(True)
        layoutscriptbuttons.addWidget(label)
        
        self.btnpause = self.app.normal_button(layoutscriptbuttons,"Pause",self.script_button_pause)
        
        layoutright.addLayout(layoutscriptbuttons)

        layoutright.addStretch()


    def script_button_pause(self):
        if self.script_execution:
            self.btnpause.setText("Continue")
            self.script_execution=False
        else:
            self.btnpause.setText("Pause")
            self.script_execution=True
            if self.script_selected==1:
                self.script_from_txt()
            elif self.script_selected==2:
                self.entry_window_script_grid()

    def script_end(self):
        self.script_execution=False
        self.script_index=None
        self.app.h5saving.save_on_acquire()
        self.btnexec.setText("Execute")
        self.labelscr.setText("")
    
    def script_button_execute(self):
        if self.app.pixis.live_mode_running or self.app.orca.live_mode_running_s:
            print("Live mode needs to be stopped before executing scripts")
        else:
            if self.script_selected==0:
                print("no script selected to execute")
                
            elif self.script_selected==1:
                if self.script_execution==False and self.script_index is None:
                    self.script_from_txt()
                else:
                    self.script_end()

            else:# self.script_selected==2:
                if self.script_execution==False and self.script_index is None:
                    self.entry_window_script_grid()
                else:
                    self.script_end()

    def sleep_method(self,time_seconds):
        self.sleep_timer=QTimer()
        self.sleep_timer.timeout.connect(self.end_sleep)
        timer_time=int(time_seconds*1000)
        self.sleep_timer.start(timer_time)

    def end_sleep(self):
        self.sleep_timer.stop()

    def check_script(self,fname):
        settings_list=[]
        double_format_keys=["spatial_acquisition_time_seconds",
                            "spectral_acquisition_time_seconds",
                            "center_wavelength_nm",
                            "stage_x_mm",
                            "stage_y_mm",
                            "sleep_seconds"]
        int_format_keys=["grating_position_int"]
        bool_format_keys=["save_spectral_image_bool"]
        comment_required=["sleep_seconds"]
        spectral_required=["spectral_acquisition_time_seconds",
                           "center_wavelength_nm",
                           "grating_position_int",
                           "save_spectral_image_bool",
                           "stage_x_mm",
                           "stage_y_mm"]
        spatial_required=["spatial_acquisition_time_seconds",
                          "stage_x_mm",
                          "stage_y_mm"]
        
        with open(fname, "r") as f:
            lines=f.read().splitlines()
        for line in lines:
            settings=dict()
            expressions=line.split(",")
            for expr in expressions:
                try:
                    key,value=expr.split(":")
                except ValueError:
                    print("ERROR missing ':'")
                    return None
                if key in double_format_keys:
                    settings[key]=np.double(value)
                elif key in int_format_keys:
                    settings[key]=int(value)
                elif key in bool_format_keys:
                    settings[key]=bool(value)
                else:
                    settings[key]=value
            if "mode" not in settings:
                print("mode is necessary in every line")
                return None
            check=True
            if settings["mode"]=="comment":
                for requirement in comment_required:
                    if requirement not in settings:
                        check=False
                        print("sleep false")
            elif settings["mode"]=="spectral":
                for requirement in spectral_required:
                    if requirement not in settings:
                        check=False
                        print("spectral false")
            elif settings["mode"]=="spatial":
                for requirement in spatial_required:
                    if requirement not in settings:
                        check=False
                        print("spatial false")
            if not check:
                print("settings requirements not fulfilled")
                return None
            
            settings_list.append(settings)
        return settings_list

    def script_from_txt(self):
        fname,ftype = QFileDialog.getOpenFileName(self, 'Open file', 
               self.app.h5saving.save_folder,"settings list (*.txt)")
        #print(fname)
        if fname:
            settings_list=self.check_script(fname)
            if settings_list is None:
                print("script includes errors")
            else:

                self.script_execution=True
                if self.script_index is None:
                    self.script_index=0
                self.btnexec.setText("Cancel")
                    
                if not self.app.h5saving.save_on_acquire_bool:
                    self.app.h5saving.save_on_acquire()
                
                
                number_of_points=len(settings_list)        
                for i in range(self.script_index,number_of_points):
                    settings=settings_list[i]
                    if "comment_text" in settings:
                        self.app.h5saving.widgetcomment.setText(settings["comment_text"])
                        self.app.h5saving.comment_edited(settings["comment_text"])
                    if "heading_text" in settings:
                        self.app.h5saving.group=settings["heading_text"]
                        self.app.h5saving.widgeth5group.setText(self.app.h5saving.group)
                    if settings["mode"]=="comment":
                        sleep_time=settings["sleep_seconds"]*1000
                        self.sleep_method(sleep_time)
                    elif settings["mode"]=="spectral":
                        self.app.pixis.acqtime_spectral=settings["spectral_acquisition_time_seconds"]
                        self.app.monochromator.wavelength=settings["center_wavelength_nm"]
                        self.app.monochromator.wavelength_edited() ###################################################
                        self.app.pixis.save_full_image=settings["save_spectral_image_bool"]
                        self.app.pixis.checkbox.setChecked(self.app.pixis.save_full_image)
                        self.app.monochromatorgrating_changed(settings["grating_position_int"]-1)
                        self.app.stage.xpos=settings["stage_x_mm"]
                        self.app.stage.ypos=settings["stage_y_mm"]
                        self.app.stage.stage_goto()

                        QApplication.processEvents()
                        if self.script_execution==False:
                            return None            
                        
                        self.app.pixis.acquire_clicked_spectral()


                    elif settings["mode"]=="spatial":
                        self.app.pixis.acqtime_spectral=settings["spatial_acquisition_time_seconds"]
                        self.app.stage.xpos=settings["stage_x_mm"]
                        self.app.stage.ypos=settings["stage_y_mm"]
                        self.app.stage.stage_goto()

                        QApplication.processEvents()
                        if self.script_execution==False:
                            return None            

                        self.app.orca.acquire_clicked_spatial()

                    
                    self.script_index+=1
                    print(str(i+1)+" from "+str(number_of_points))
                    self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                    
                    QApplication.processEvents()
                    if self.script_execution==False:
                        return None
                    
                self.script_end()

            
    def script_changed(self,i):
        self.script_selected=i

            
    def entry_window_script_grid(self):
        if self.script_index is None:
            self.w = self.app.entrymask6(self.app.stage)
            self.w.location_on_the_screen()
            self.w.exec()

        # execute script
        if self.script_execution:
            if self.script_index is None:
                self.script_index=0
            self.btnexec.setText("Cancel")
            if not self.app.h5saving.save_on_acquire_bool:
                self.app.h5saving.save_on_acquire()
            number_of_points=len(self.script_positions_x)        
            for i in range(self.script_index,number_of_points):
                self.app.stage.xpos=self.script_positions_x[i]
                self.app.stage.ypos=self.script_positions_y[i]
                self.app.stage.stage_goto()      
                xcheck,ycheck=self.stage.get_position()
                print("check position: "+str(xcheck)+","+str(ycheck))
                
                QApplication.processEvents()
                if self.script_execution==False:
                    return None
                
                if self.script_selected==2:
                    self.app.orca.acquire_clicked_spatial()
                elif self.script_selected==3:
                    self.app.pixis.acquire_clicked_spectral()
                else:
                    self.app.orca.acquire_clicked_spatial()
                    self.app.threadpool.waitForDone()
                    self.app.pixis.acquire_clicked_spectral()
                
                self.app.threadpool.waitForDone()
                self.script_index+=1
                print(str(i+1)+" from "+str(number_of_points))
                self.labelscr.setText(str(i+1)+"/"+str(number_of_points))
                QApplication.processEvents()
                if self.script_execution==False:
                    return None
                    
            self.script_end()