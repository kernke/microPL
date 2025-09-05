import h5py
import numpy as np
import os

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QFileDialog,QLabel,QVBoxLayout


class Saving:
    def __init__(self,app):
        self.save_on_acquire_bool=False
        self.app=app

        self.acq_number=0
        #defaults start
        self.acq_name_prefix="acq_" 
        self.group="measurement" 
        self.file_name=r'microPL_' 
        self.save_folder=r"C:\Users\user\Documents\Data\test" 
        #defaults end
        self.acq_name=self.acq_name_prefix+str(self.acq_number).zfill(5)
        self.h5struc=self.group+"/"+self.acq_name
        try:
            allfiles=os.listdir(self.save_folder)
        except:
            print("save dummy mode")
            allfiles=["just_one_file"]
        filenumbers=[-1]
        for i in allfiles:
            if "microPL_" == i[:8]:
                if i[8:-3].isnumeric():
                    filenumbers.append(int(i[8:-3]))
        newnumber=int(np.max(filenumbers)+1)
        self.file_name+=str(newnumber)        
        self.filepath=os.path.join(self.save_folder, self.file_name+".h5")

    def write_to_h5(self,data):
        if self.group=="":
            print("empty group not valid, saved as:")
            self.group="measurement"
            print(self.group)   
            self.widgeth5group.setText(self.group)
        if self.acq_name=="":
            print("empty name not valid, saved as:")
            self.acq_name=self.acq_name_prefix+str(self.acq_number).zfill(5)
            print(self.acq_name)            
        self.h5struc=self.group+"/"+self.acq_name#+str(self.acq_number).zfill(5)
        with h5py.File(self.filepath, 'a') as hf:
            for i in data:
                if i == "unsaved":
                    data[i]=False
                else:
                    dt = h5py.string_dtype(encoding='utf-8')
                    if isinstance(data[i], str):
                        hf.create_dataset(self.h5struc+"/"+i, data=data[i], dtype=dt)
                    else:
                        hf[self.h5struc+"/"+i]=data[i]
            
        self.acq_number+=1
        self.acq_name=self.acq_name_prefix+str(self.acq_number).zfill(5)
        self.h5struc=self.group+"/"+self.acq_name#+str(self.acq_number).zfill(5)
        self.widgeth5name.setText(self.acq_name)
        self.app.add_log("(in "+self.group+")")
        self.app.add_log(self.acq_name+" saved")
        print("saved")

    def check_h5(self):
        check=True
        with h5py.File(self.filepath, 'a') as hf:    
            if self.h5struc in hf:
                self.app.save_warning()
                check=False
        return check


    def save_to_h5_spectral(self):
        if not self.app.metadata_spectral["unsaved"]:
            #print("already saved before")
            self.app.add_log("already saved before")
        else:
            if self.check_h5():
                profile = self.app.pixis.roi.getArrayRegion(self.app.pixis.img.image, img=self.app.pixis.img)
                self.app.metadata_spectral["intensity"]=profile.mean(axis=-1)
                self.app.metadata_spectral["wavelength"]=self.app.monochromator.spectrum_x_axis
                if self.app.pixis.save_full_image:
                    self.app.metadata_spectral["image"]=self.app.pixis.img_data#.image

                self.write_to_h5(self.app.metadata_spectral)
                self.app.metadata_spatial["comment"]=""
                self.app.metadata_spectral["comment"]=""
                self.app.metadata_timeline["comment"]=""
                self.widgetcomment.setText("")



    def save_to_h5_spatial(self):
        if not self.app.metadata_spatial["unsaved"]:
            #print("already saved before")
            self.app.add_log("already saved before")
        else:
            if self.check_h5():
                self.app.metadata_spatial["image"]=self.app.orca.img_data#.image
                self.write_to_h5(self.app.metadata_spatial)
                self.app.metadata_spatial["comment"]=""
                self.app.metadata_spectral["comment"]=""
                self.app.metadata_timeline["comment"]=""
                self.widgetcomment.setText("")

    def save_to_h5_timeline(self):
        if self.app.metadata_timeline["unsaved"]:
            if self.check_h5():
                self.app.metadata_timeline["mode"]="timeline"
                self.app.metadata_timeline["time_s"]=self.app.keysight.timeline_list
                self.app.metadata_timeline["voltage_V"]=self.app.keysight.voltage_list
                self.app.metadata_timeline["current_A"]=self.app.keysight.currentA_list
                self.write_to_h5(self.app.metadata_spatial)
                self.app.metadata_spatial["comment"]=""
                self.app.metadata_spectral["comment"]=""
                self.app.metadata_timeline["comment"]=""
                self.widgetcomment.setText("")
                self.app.last_saved_timeline_length=len(self.app.keysight.timeline_list)
        else:
            self.app.add_log("already saved before")


    def save_comment(self):
        if self.check_h5():
            self.app.metadata_timeline["mode"]="comment"
            self.write_to_h5(self.app.metadata_timeline)
            self.app.metadata_timeline["unsaved"]=True
            self.app.metadata_spatial["comment"]=""
            self.app.metadata_spectral["comment"]=""
            self.app.metadata_timeline["comment"]=""
            self.widgetcomment.setText("")

    
    def save_on_acquire(self):
        self.save_on_acquire_bool=not self.save_on_acquire_bool
        if self.save_on_acquire_bool:
            self.app.pixis.btnacq_spectral.setStyleSheet("background-color: green")
            self.app.orca.btnacq_spatial.setStyleSheet("background-color: green")
            
            self.btnsaveacq.setStyleSheet("background-color: green")
            self.btnsaveacq.setText("Stop Save on Acq./Live")
            self.app.pixis.btnsave_spectral.setStyleSheet("background-color: red")
            self.app.orca.btnsave_spatial.setStyleSheet("background-color: red")

        else:
            self.app.pixis.btnacq_spectral.setStyleSheet("background-color: lightGray")
            self.app.orca.btnacq_spatial.setStyleSheet("background-color: lightGray")
            
            self.btnsaveacq.setStyleSheet("background-color: lightGray")
            self.btnsaveacq.setText("Save on Acquire/Live")
            self.app.pixis.btnsave_spectral.setStyleSheet("background-color: lightGray")
            self.app.orca.btnsave_spatial.setStyleSheet("background-color: lightGray")
            



    def h5group_edited(self,s):
        self.group=s

    def h5name_edited(self,s):
        self.acq_name=s


    def save_warning(self):
        self.w = self.app.warnwindow()#    WarnWindow()
        self.w.setWarnText("This h5-path already exists")
        self.w.location_on_the_screen()
        self.w.show()
     
    def set_filepath(self):
        filename, _ = QFileDialog.getSaveFileName(
            self.app, "Save Data", self.filepath, "data (*.h5)",
            options=QFileDialog.DontConfirmOverwrite
        )
        if filename:
            self.filepath=filename
            self.labelsave.setText("..."+self.filepath[-32:])

    def comment_edited(self,s):
        if s:
            self.app.metadata_spatial["comment"]=s
            self.app.metadata_spectral["comment"]=s
            self.app.metadata_timeline["comment"]=s

    def expand(self):
        if not self.expanded:
            self.expanded=True
            self.app.set_layout_visible(self.dropdown,True)
        else:
            self.expanded=False
            self.app.set_layout_visible(self.dropdown,False)

    def save_ui(self,layoutright):
        self.expanded=False
        self.app.heading_label(layoutright,"Saving   ",self.expand)
        
        self.dropdown=QVBoxLayout()

        layoutsavetext=QHBoxLayout()
        labelsave = QPushButton()
        labelsave.setStyleSheet("background-color: lightGray; text-align: left")
        labelsave.setText("  ..."+self.filepath[-32:]+" ")
        labelsave.clicked.connect(self.set_filepath)
        self.labelsave=labelsave
        layoutsavetext.addWidget(labelsave)

        label = QLabel("file path")
        label.setStyleSheet("color:white")
        layoutsavetext.addWidget(label)
        self.dropdown.addLayout(layoutsavetext)

        layoutsavelabels=QHBoxLayout()

        label = QLabel("Heading/Group")
        label.setStyleSheet("color:white")
        layoutsavelabels.addWidget(label)
        layoutsavelabels.addStretch()
        label = QLabel("Acquisition Name")
        label.setStyleSheet("color:white")
        layoutsavelabels.addWidget(label)

        self.dropdown.addLayout(layoutsavelabels)

        layoutsaveh5=QHBoxLayout()        
        self.widgeth5group = QLineEdit()
        self.widgeth5group.setStyleSheet("background-color: lightGray")
        self.widgeth5group.setText(self.group)
        layoutsaveh5.addWidget(self.widgeth5group)
        self.widgeth5group.textEdited.connect(self.h5group_edited)

        layoutsaveh5.addStretch()
        label = QLabel("         ")
        layoutsaveh5.addWidget(label)
        layoutsaveh5.addStretch()

        self.widgeth5name = QLineEdit()
        self.widgeth5name.setStyleSheet("background-color: lightGray")
        self.widgeth5name.setText(self.acq_name)
        layoutsaveh5.addWidget(self.widgeth5name)
        self.widgeth5name.textEdited.connect(self.h5name_edited)

        self.dropdown.addLayout(layoutsaveh5)

        layoutcomment=QHBoxLayout()
        self.widgetcomment = QLineEdit()
        self.widgetcomment.setStyleSheet("background-color: lightGray")
        self.widgetcomment.setText("")
        layoutcomment.addWidget(self.widgetcomment)
        self.widgetcomment.textEdited.connect(self.comment_edited) 

        label = QLabel("comment")
        label.setStyleSheet("color:white")
        layoutcomment.addWidget(label)
        self.dropdown.addLayout(layoutcomment)

        layoutsavebuttons=QHBoxLayout()

        self.btnsaveacq=self.app.normal_button(layoutsavebuttons,"Save on Acquire/Live",self.save_on_acquire)
        self.btnsaveacq.setFixedWidth(130)
        layoutsavebuttons.addStretch()
        self.btnsavecomment=self.app.normal_button(layoutsavebuttons,"Save Comment only",self.save_comment)
        self.btnsavecomment.setFixedWidth(130)

        self.dropdown.addLayout(layoutsavebuttons) 

        layoutright.addLayout(self.dropdown)
        self.app.set_layout_visible(self.dropdown,False)
        layoutright.addItem(self.app.vspace)
        