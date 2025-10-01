import numpy as np

def multi_current_mapping(currents,boundary_points_stage,spatial=True,spectral=False):
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="2"
    lines.append("filter : "+filter_wheel_open_position)
    if not spectral:
        lines.append("spectral_shutter_mode : closed")
    else:
        lines.append("spectral_shutter_mode : open")

    for i in range(len(currents)):
        line="stage_mapping : "
        line+= "spectral_bool : "+str(spectral)+" , "
        line+= "spatial_bool : "+str(spatial)+" , "
        
    

def multi_step_IV(steps,boundary_points_mA,spatial=True,spectral=True):
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="2"
    lines.append("filter : "+filter_wheel_open_position)
    if not spectral:
        lines.append("spectral_shutter_mode : closed")
    else:
        lines.append("spectral_shutter_mode : open")



def acq_pause_acq_sequence(timestep,spatial=True,spectral=True):
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="2"
    lines.append("filter : "+filter_wheel_open_position)
    if not spectral:
        lines.append("spectral_shutter_mode : closed")
    else:
        lines.append("spectral_shutter_mode : open")

