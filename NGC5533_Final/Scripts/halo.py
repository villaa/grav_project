#Imports
#import numpy as np
#import h5py as h5

#Constants
#G = 4.300e-6                                                #gravitational constant (kpc/solar mass*(km/s)^2)
#rho00 = 0.31e9                                              #central surface density (solar mass/kpc^3)

#Savedata Naming Values
#r0id = "varray_"+str(r0[0])+"-"+str(r0[len(r0)-1])+"_"+str(len(r0))+".hdf5"
#location = "Inputs/r0id"
r00val = "r00"+str(rho00)

#Load if available, else create
#try:
#    saved = h5.File(location,"w")
#except OSError:
#    saved = h5.File(location,"r")

try:
    grp = saved.create_group("halo")
except ValueError:
    grp = saved["halo"]

try:     
    #Open
    vcdmd = grp[r00val]
    #Read
    vcdmr = vcdmd[:]
except KeyError:
    #using a velocity equation from the paper "Dark halo properties from rotation curves" by Jimenez et.al.
    vcdm = lambda r: np.sqrt(4*np.pi*G*rho00*(rc**2)*(1-((rc/r)*np.arctan(r/rc))))       #eq 9 from Jimenez paper #rho00
    
    #Calculate
    vcdmr = np.zeros(len(r0))
    for i,n in enumerate(r0):
        vcdmr[i] = vcdm(n)
    
    #Save
    grp.create_dataset(r00val,data=vcdmr)
