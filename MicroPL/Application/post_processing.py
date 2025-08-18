# -*- coding: utf-8 -*-

import numpy as np
import h5py


def measurement_groups_from_file(file_name):
    """obtain a list of the measurement groups
    """
    with h5py.File(file_name,'r') as hf:
        measurementlist=list(hf.keys())
        for i in hf.keys():
            print(i)
            print("containing "+str(len(hf[i].keys()))+" acquisitions")
            print()
            
    return measurementlist

def grid_mapping(file_name,measurement_h5name,full_chip_image=False):
    """obtain 2d-structures from the list of acquisitions using the 'grid-mapping' script
    """
    spectra=[]
    xpositions=[]
    ypositions=[]
    
    with h5py.File(file_name,'r') as hf:

        for i in range(len(hf[measurement_h5name])):
            key="acq_"+str(i).zfill(3)
            spectra.append(hf[measurement_h5name+"/"+key+"/spectrum"][:])
            xpositions.append(hf[measurement_h5name+"/"+key+"/x"][()])
            ypositions.append(hf[measurement_h5name+"/"+key+"/y"][()])
            
    mapshape=len(np.unique(xpositions)),len(np.unique(ypositions))
    spectra=np.array(spectra)
    xpositions=np.array(xpositions)
    ypositions=np.array(ypositions)
    
    xsortindex=np.argsort(xpositions)
    xsorted=xpositions[xsortindex]
    x2d=np.reshape(xsorted,mapshape)
    
    y2dunsorted=np.reshape(ypositions[xsortindex],mapshape)
    spec2dunsorted=np.reshape(spectra[xsortindex,:],[mapshape[0],mapshape[1],1024])
    
    y2d=np.zeros(y2dunsorted.shape)
    spec2d=np.zeros(spec2dunsorted.shape)
    for i in range(mapshape[0]):
        ysortindex=np.argsort(y2dunsorted[i])
        y2d[i]=y2dunsorted[i][ysortindex]
        spec2d[i,:,:]=spec2dunsorted[i,ysortindex,:]
    return x2d,y2d,spec2d
        