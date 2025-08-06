# coding=windows-1252
# =====================================================================
# Example how to use Tango DLL in conjunction with Python version 3.10.5
# =====================================================================
import ctypes
import sys
import re
from ctypes import *  # import ctypes (used to call DLL functions)

class Stage():
    def __init__(self):
        self.m_Tango = cdll.LoadLibrary(r"C:\Users\user\Documents\Python\MicroPL_package\MicroPL\stage_scripts\Tango_DLL.dll")  # give location of dll (current directory)

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
        