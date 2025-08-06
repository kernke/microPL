import pylablib as pll
from pylablib.devices import PrincetonInstruments
import time
import pyqtgraph as pg
import pprint
import numpy as np

class Pixis():
    def __init__(self):
        pll.par["devices/dlls/picam"] = r"C:\Program Files\Common Files\Princeton Instruments\Picam\Runtime"
        cameras = PrincetonInstruments.list_cameras()
        print('Camera found:', cameras)

        self.cam = PrincetonInstruments.PicamCamera('09166914')
        #pprint.pp(dir(cam))

        #def pixelfmt():
        #self.pix_format = cam.get_attribute_value("Pixel Format")  # get the current pixel format

    
    def acquire(self, t, x0,x1,y0,y1, hbin,vbin,show=True):
        self.cam.set_exposure(t)
        attr = self.cam.get_exposure()
        pprint.pp("Exposure time: " + str(attr))
        self.cam.set_roi(x0, x1, y0, y1, hbin, vbin)
        self.cam.setup_acquisition(mode='snap') # mode= [snap, sequence], [nframes = X]
        self.cam.start_acquisition()
        self.cam.wait_for_frame()
        img = self.cam.read_newest_image()
        self.cam.stop_acquisition()
        
        
        pprint.pp(np.shape(img))
        if show:
            pg.image(img)
        return img
        
    def chip_temp(self):
        temp = self.cam.get_attribute_value("Sensor Temperature Reading")
        pprint.pp("Sensor Temperature: " + str(temp))
        temp_status = self.cam.get_attribute_value("Sensor Temperature Status")
        pprint.pp("Temperature status: " + str(temp_status))




    def close(self):
        self.cam.close()
        print("Camera disconnected")
        
#shutter_timing = cam.get_attribute_value("Shutter Timing Mode")
#pprint.pp("Shutter timing: " + str(shutter_timing))
#attr = cam._list_attributes()
#pprint.pp(attr)
#cam.setup_shutter("open")