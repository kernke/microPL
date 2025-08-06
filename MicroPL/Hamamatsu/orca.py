from pylablib.devices import DCAM

class Orca():
    def __init__():
        self.cam = DCAM.DCAMCamera(idx=0)

    def set_exposure(self,exposure_time):
        self.cam.set_exposure(exposure_time)

    def acquire(self):
        image = self.cam.grab(1)[0]
        return image

    def disconnect(self):
        self.cam.close()