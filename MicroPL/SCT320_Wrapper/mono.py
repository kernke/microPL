"""
Example showing how to communicate with a SCT320 monochromator from Princeton Instruments.
https://msl-equipment.readthedocs.io/en/latest/index.html
https://msl-equipment.readthedocs.io/en/latest/_api/msl.equipment.resources.princeton_instruments.arc_instrument.html
"""
import pprint
from msl.equipment import (
    EquipmentRecord,
    ConnectionRecord,
    Backend,
)
from msl.equipment.exceptions import PrincetonInstrumentsError

class SCT320():
    def __init__(self):
        record = EquipmentRecord(
            manufacturer='Princeton Instruments',
            model='SCT320',  # update for your device
            connection=ConnectionRecord(
                address='COM7',  # update for your device
                backend=Backend.MSL,
                properties={
                    'sdk_path': r'C:\Users\user\Documents\Python\SCT320_Wrapper\ARC_Instrument_x64.dll',  # update
                }
            )
        )

        # Connect to the monochromator
        self.mono = record.connect()

        self.focal_length_mm= 327
        self.pixel_width_microns=26
        self.alignment_delta=0



        #pprint.pp(dir(self.mono))

        # Print some information about the monochromator
        print('Model: {}'.format(self.mono.get_mono_model()))
        print('Serial: {}'.format(self.mono.get_mono_serial()))
        #print('Focal length: {}'.format(self.mono.get_mono_focal_length()))
        #print('Half angle: {}'.format(self.mono.get_mono_half_angle()))
        #print('Detector angle: {}'.format(self.mono.get_mono_detector_angle()))
        #print('Is double Monochromator? {}'.format(self.mono.get_mono_double()))
        #print('Is subtractive double Monochromator? {}'.format(self.mono.get_mono_double_subtractive()))
        #print('Turret: {}'.format(self.mono.get_mono_turret()))
        #print('Max number of Turrets: {}'.format(self.mono.get_mono_turret_max()))
        #print('Grating: {}'.format(self.mono.get_mono_grating()))
        #print('Max number of Gratings: {}'.format(self.mono.get_mono_grating_max()))
        # Grating information
        #print('Turret gratings: {}'.format(self.mono.get_mono_turret_gratings()))
        
    def disconnect(self):
        self.mono.disconnect()
        print('SCT Disconnected')

    def gratings(self):
        indices=[]
        densities=[]
        blazes=[]        
        for index in range(1, 7):#self.mono.get_mono_turret_gratings()+1):
            indices.append(index)
            density = self.mono.get_mono_grating_density(index)
            densities.append(density)
            blaze = self.mono.get_mono_grating_blaze(index)
            blazes.append(blaze)
            #print('Grating: {}, Density: {}, Blaze: {}'.format(index, density, blaze))
        return indices,densities,blazes
            
    def get_wavelength(self):
        # Wavelength information (centerwavelength)
        nm = self.mono.get_mono_wavelength_nm()
        min_nm = self.mono.get_mono_wavelength_min_nm()
        cutoff_nm = self.mono.get_mono_wavelength_cutoff_nm()
        print('Wavelength at {} nm (Min: {} nm, Max: {} nm)'.format(nm, min_nm, cutoff_nm))
        return nm

    def set_wavelength(self, WL):

        print('Setting the wavelength to '+ str(WL) +'nm...')
        self.mono.set_mono_wavelength_nm(WL)
        print('  Wavelength at {} nm'.format(self.mono.get_mono_wavelength_nm()))

    def set_grating(self,G):
    # Set the grating to position G
        print('Setting the Grating to position'+ str(G) +'...')
        self.mono.set_mono_grating(G)
        index = self.mono.get_mono_grating()
        density = self.mono.get_mono_grating_density(index)
        blaze = self.mono.get_mono_grating_blaze(index)
        print('  Grating at position {} -> Density: {}, Blaze: {}'.format(index, density, blaze))
        
    def get_grating(self):
        index = self.mono.get_mono_grating()
        print('Grating: ' + str(index) + '.' )
        density = self.mono.get_mono_grating_density(index)
        blaze = self.mono.get_mono_grating_blaze(index)
        print('  Grating at position {} -> Density: {}, Blaze: {}'.format(index, density, blaze))
        return index,density,blaze
    
    #def get_dispersion(self):
    #    det_range = self.mono.get_det_range(0)
    #    print(det_range)

        # 1: 600 l - 0.123 nm/pix
        # 2: 300 l - 0.254 nm/pix
        # 3: 150 l - 0.514 nm/pix

        # 4: 
        # 5: 1800    0.03 nm/pix
        # 6: 150
        
# Diverter Mirror information
#for index in range(1, 5):
#    try:
#        mono.get_mono_diverter_valid(index)
#    except PrincetonInstrumentsError:
#        print('Diverter mirror {} is not valid'.format(index))
#    else:
#        position = mono.get_mono_diverter_pos(index)
#        print('Diverter mirror {} is motorized and at position {}'.format(index, position))
# Slit information
#for index in range(1, 9):
#    try:
#        name = mono.mono_slit_name(index)
#        typ = mono.get_mono_slit_type(index)
#        width = mono.get_mono_slit_width(index)
#        max_width = mono.get_mono_slit_width_max(index)
#    except PrincetonInstrumentsError:
#        print("Slit {}: 'Invalid Slit'")
#    else:
#        print('Slit {}: Name={!r}, Type={!r}, Width={} um, Max={} um'.format(index, name, typ, width, max_width))

# Filter wheel information
#if mono.get_mono_filter_present():
#    pos = mono.get_mono_filter_position()
#    min_pos = mono.get_mono_filter_min_pos()
#    max_pos = mono.get_mono_filter_max_pos()
#    print('Filter wheel at position {} (Min: {}, Max: {})'.format(pos, min_pos, max_pos))
#else:
 #   print('The Monochromator does not have a filter wheel.')

# Shutter information
#if mono.get_mono_shutter_valid():
#    if mono.get_mono_shutter_open():
#        print('Shutter is open')
#    else:
#        print('Shutter is closed')
#else:
#    print('The Monochromator does not have a shutter.')



# Set the filter wheel to position 3
#if mono.get_mono_filter_present():
#    print('Setting the Filter Wheel to position 3...')
#    mono.set_mono_filter_position(3)
#    print('  Filter wheel at position {}'.format(mono.get_mono_filter_position()))

# Set the Front Entrance slit to be a width of 1000 um
#print('Setting Slit 2 (Front Entrance) to a width of 1000 um...')
#mono.set_mono_slit_width(2, 1000)
#print('  Slit 2 is at {} um'.format(mono.get_mono_slit_width(2)))



# Disconnect from the monochromator
#mono.disconnect()