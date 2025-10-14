import numpy as np

def multi_current_mapping(currents_mA,boundary_points_stage,spatial=True,spectral=False,max_voltage_V=30):
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="3"
    lines.append("filter : "+filter_wheel_open_position)
    if not spectral:
        lines.append("spectral_shutter_mode : normal")
    else:
        lines.append("spectral_shutter_mode : open")

    for i in range(len(currents_mA)):
        lines.append("current_mA : "+str(currents_mA[i]))
        if i==0:
            lines.append("voltage_V : "+str(max_voltage_V))
            lines.append("electric_output_bool : True")
        line="stage_mapping : "
        line+= "spectral_bool : "+str(spectral)+" , "
        line+= "spatial_bool : "+str(spatial)+" , "
        line+= "x_min_mm : "+str(boundary_points_stage[0])+" , "
        line+= "x_max_mm : "+str(boundary_points_stage[1])+" , "
        line+= "x_num_int : "+str(boundary_points_stage[2])+" , "
        line+= "y_min_mm : "+str(boundary_points_stage[3])+" , "
        line+= "y_max_mm : "+str(boundary_points_stage[4])+" , "
        line+= "y_num_int : "+str(boundary_points_stage[5])   

        lines.append(line) 


    if spectral:
        lines.append("spectral_shutter_mode : normal")
    lines.append("electric_output_bool : False")
    return lines


def multi_step_IV(steps_mA,boundary_points_mA,settling_time_s,spatial=True,spectral=True):
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="3"
    lines.append("filter : "+filter_wheel_open_position)
    if not spectral:
        lines.append("spectral_shutter_mode : normal")
    else:
        lines.append("spectral_shutter_mode : open")

    for i in range(len(steps_mA)):
        line="measure_iv_curve_set_currents : "
        line+= "spectral_bool : "+str(spectral)+" , "
        line+= "spatial_bool : "+str(spatial)+" , "
        bp=boundary_points_mA[i]
        line+="step_current_mA : "+str(steps_mA[i])+" , "
        line+="start_current_mA : "+str(bp[0])+" , "
        line+="end_current_mA : "+str(bp[1])+" , "
        line += "settling_time_s : "+str(settling_time_s)

        lines.append(line) 


    if spectral:
        lines.append("spectral_shutter_mode : normal")
    return lines

def acq_pause_acq_sequence(current_mA,timestep_s,electric_timestep_s,timerange_s,
                            spatial=True,spectral=True,max_voltage_V=30):
    #timerange_s should be a multiple of timestep_s, which should be a multiple of electric_timestep_s
    lines=[]
    filter_wheel_open_position="1"
    filter_wheel_closed_position="3"

    if not spectral:
        lines.append("spectral_shutter_mode : normal")
    else:
        lines.append("spectral_shutter_mode : open")

    repetitions=int(timerange_s/timestep_s)
    elec_repetitions=int(timestep_s/electric_timestep_s)

    lines.append("current_mA : "+str(current_mA))
    lines.append("voltage_V : "+str(max_voltage_V))
    lines.append("electric_output_bool : True")

    lines.append("filter : "+filter_wheel_open_position)
    if spatial:
        lines.append("spatial_acquire")
    if spectral:
        lines.append("spectral_acquire")
    lines.append("filter : "+filter_wheel_closed_position)

    lines.append("electric_measurement_to_timeline")

    for i in range(repetitions):

        for j in range(elec_repetitions):
            lines.append("sleep_s : "+str(electric_timestep_s))
            lines.append("electric_measurement_to_timeline")

        lines.append("filter : "+filter_wheel_open_position)

        if spatial:
            lines.append("spatial_acquire")
        if spectral:
            lines.append("spectral_acquire")
        lines.append("filter : "+filter_wheel_closed_position)

    if spectral:
        lines.append("spectral_shutter_mode : normal")
    lines.append("electric_output_bool : False")
    return lines
