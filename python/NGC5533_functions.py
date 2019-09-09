################################
########### Imports ############
################################
import sys
import numpy as np
import scipy.special as ss
import scipy.optimize as so
import scipy.integrate as si
import scipy.interpolate as inter
try:
    import h5py as h5
    h5py = 1
except ModuleNotFoundError:
    h5py = 0
    print("Could not find h5py. Datasets will not be able to be saved or loaded using NGC5533_functions.")

################################
########## Settings ############
################################    

options={'limit':100}     #Sets maximum subdivisions to 100 for integration instead of 50
x = np.linspace(0,10,100) #Default radius array

################################
########## Constants ###########
################################

#---------Definitely Constant---------
G = 4.30091e-6    #gravitational constant (kpc/solar mass*(km/s)^2)
rhocrit = 9.3e-18 #critical density of the Universe (kg/km^3)

#---------Measured Directly-----------
L = 3.27e10                              #luminosity
absmag = -22.02                          #absolute magnitude
magsun = 4.42                            #absolute magnitude of the sun
L0 = np.power(10, (0.4*(magsun-absmag))) #Absolute Magnitude to luminosity

#---------Measured Indirectly---------
ups = 2.8                         #mass-to-light ratio (from Rotation Curves of Sersic Bulges paper)
q = 0.33                          #intrinsic axis ratio
e2 = 1-(q**2)
i = 45*(np.pi/180)                #inclination angle
h_rc = 1.4                        #core radius (kpc)

c = 1e-12                         #concentration parameter
Mvir = 1e11*((c/(11.7))**(-40/3)) #virial mass (in solar mass) solved from eq(5)
Mbh_def = 2.7e9                   #Black Hole mass

#---------Definitely Variable---------
n_c = 2.7
h_c = 8.9                           #radial scale-length (kpc)
rho00_c = 0.31e9                    #central surface density (solar mass/kpc^3)

#---------Uncategorized-------------------
re = 2.6                                                 #1kpc
epsdisk = 5.0                                            #from Noordermeer's paper
rs = (1/c)*(((3*Mvir)/((4*np.pi*100*rhocrit)))**(1/3))   #scale radius (kpc)
rho_s = (100/3)*((c**3)/(np.log(1+c)-(c/(1+c))))*rhocrit #characteristic density
h_gamma = 0

################################
########### Saving #############
################################

def savedata(xvalues,yvalues,group,dataset,path='./',file='Inputs.hdf5'):
    if h5py == 1:
        saved = h5.File(path+file,'a')
        if group in ['Disk', 'disc', 'Disc', 'd', 'D']:
            group = 'disk'
            print("Group name set to 'disk'.")
        if group in ['bh','Bh','BH','Black Hole','BlackHole','Blackhole,','Black hole','black hole','Black Hole']:
            group = 'blackhole'
            print("Group name set to 'blackhole'.")
        if group in ['dm','DM','Dm','Dark Matter','Dark matter','dark matter','h','H','Halo','darkmatter','Darkmatter','DarkMatter']:
            group = 'halo'
            print("Group name set to 'halo'.")
        if group in ['b','B','Bulge']:
            group = 'bulge'
            print("Group name set to 'bulge'.")
        if group in ['t','T','Total']:
            group = 'total'
            print("Group name set to 'total'.")
        try:
            grp = saved.create_group(group)
            grp.create_dataset(dataset,data=[xvalues,yvalues])
        except:
            grp = saved[group]
            try:
                grp.create_dataset(dataset,data=[xvalues,yvalues])
            except RuntimeError:
                return loaddata(dataset,group,path,file)
                print("Already exists! Loaded data.")
        saved.close()
        print("Saved.")
    if h5py == 0:
        print("ERROR: h5py was not loaded.")
        return 1
    
def loaddata(group,dataset,path='./',file='Inputs.hdf5'):
    if h5py == 1:
        saved = h5.File(path+file)
        if group in ['Disk', 'disc', 'Disc', 'd', 'D']:
            group = 'disk'
            print("Group name set to 'disk'.")
        if group in ['bh','Bh','BH','Black Hole','BlackHole','Blackhole,','Black hole','black hole','Black Hole']:
            group = 'blackhole'
            print("Group name set to 'blackhole'.")
        if group in ['dm','DM','Dm','Dark Matter','Dark matter','dark matter','h','H','Halo','darkmatter','Darkmatter','Dark Matter']:
            group = 'halo'
            print("Group name set to 'halo'.")
        if group in ['b','B','Bulge']:
            group = 'bulge'
            print("Group name set to 'bulge'.")
        if group in ['t','T','Total']:
            group = 'total'
            print("Group name set to 'total'.")
        #try:
        grp = saved[group]
        dset = grp[dataset]
        #except KeyError:
        #    print("No such group! Aborting.")
        #    saved.close()
        #    sys.exit
        a = dset[:]
        return a
        saved.close()
    #Placeholder; I will design this to store information at a later date.
    if h5py ==0:
        print("ERROR: h5py was not loaded.")
        return 1

################################
######### Black Hole ###########
################################

def bh_v(r,M=Mbh_def,save=False,load=False,**kwargs): #M in solar masses, r in kpc
    if save:
        a = np.sqrt(G*M/r)
        savedata(r,a,'blackhole','Mbh'+str(M),**kwargs)
        return a
    elif load:
        return loaddata('blackhole','Mbh'+str(M),**kwargs)
    else:
        a = np.sqrt(G*M/r)
        if isinstance(a,list) or isinstance(a,np.ndarray):
            a[np.isnan(a)] = 0
        return a
    
################################
########### Bulge ##############
################################

#I'm not sure how many of these we need to be defined -- I kept everything that was called outside of another function.
#We can condense the number of functions once we know for certain if there are things we don't need again.

def b_gammafunc(x,n=n_c):
    return ss.gammainc(2*n,x)*ss.gamma(2*n)-0.5*ss.gamma(2*n)
b_root = so.brentq(b_gammafunc,0,500000,rtol=0.000001,maxiter=100) #come within 1% of exact root within 100 iterations

def b_I0(n=n_c):
    return L*(b_root**(2*n))/(re**2*2*np.pi*n*ss.gamma(2*n))
def b_r0(n=n_c):
    return re/np.power(b_root,n)

def b_innerintegral(m,n=n_c):
    f = lambda x,m,n: np.exp(-np.power(x/b_r0(n), (1/n)))*np.power(x/b_r0(n), 1/n-1)/(np.sqrt(x**2-m**2)) #Inner function
    return si.quad(f, m, np.inf,args=(m,n))[0]
b_innerintegralv = np.vectorize(b_innerintegral)

def b_vsquare(r,n=n_c):
    C = lambda n: (4*G*q*ups*b_I0(n))/(b_r0(n)*np.float(n))*(np.sqrt((np.sin(i)**2)+(1/(q**2))*(np.cos(i)**2)))
    h = lambda m,r,n: C(n)*b_innerintegral(m,n)*(m**2)/(np.sqrt((r**2)-((m**2)*(e2)))) #integrate outer function
    return si.quad(h, 0, r, args=(r,n))[0]
def b_vsquarev(r,n=n_c):
    a = np.vectorize(b_vsquare)
    return a(r,n)

def b_v(r,n=n_c,save=False,load=False,**kwargs):
    if save:
        a = b_vsquarev(r,n)**(1/2)
        savedata(r,a,'bulge','n'+str(n),**kwargs)
        return a
    elif load:
        return loaddata('bulge','n'+str(n),**kwargs)
    else:
        a = b_vsquarev(r,n)**(1/2)
        return a

################################
############ Halo ##############
################################

def h_rhat(r,z):               #r-hat from Casertano eq(9)
    return np.sqrt((r**2)+(z**2))

def h_rho(r,rho00=rho00_c,rc=h_rc): #Isothermal Density Profile
    return rho00*((1+((r/rc)**2))**(-1))
    
def h_vcasertano(r,z,rc=h_rc,rho00=rho00_c,gamma=h_gamma):                       #Velocity
    v0h = lambda r,rho00,rc,z: np.sqrt(h_rho(r,rho00,rc)*4*np.pi*G*(h_rhat(r,z)**2)) #eq 9 casertano
    return v0h(r,rho00,rc,z)*((r/rc)**gamma)                                     #eq 10 casertano

def h_vjimenez(r,rc=h_rc,rho00=rho00_c):
    return np.sqrt(4*np.pi*G*rho00*(rc**2)*(1-((rc/r)*np.arctan(r/rc))))

def h_vNFW(r,save=True):
    rho = lambda r: rho_s/((r/rs)*((1+r/rs)**2))
    f = lambda R: 4*np.pi*rho(R)*(R**2)          #NFW Density Profile
    mdm = lambda r: si.quad(f, 0, r)[0]          #M(r)
    vdm2 = lambda r: (G*mdm(r))/r                #v^2: GM(r)/r
    vdm2v = np.vectorize(vdm2)
    if save:
        a = np.sqrt(vdm2v(r))
        savedata(r,a,'halo','n'+str('PLACEHOLDER'),**kwargs)
        return a
    elif load:
        return loaddata('halo','n'+str('PLACEHOLDER'),**kwargs)
    else:
        return np.sqrt(vdm2v(r))

def h_viso(r,rc=h_rc,rho00=rho00_c):
    return np.sqrt(4*np.pi*G*rho00*(rc**2)*(1-((rc/r)*np.arctan(r/rc))))
h_v = h_viso
        
        
################################
############ Disk ##############
################################

#----- To Fit For --------
#h, rho00

#----- Multiples of h ----
z0 = lambda h: 0.2*h                        #half-thickness (kpc)
R = lambda h: 4*h                           #cut-off radius (kpc)
d = lambda h: 0.2*h                         #cut-off length upper limits (kpc)

#----- Functions ---------

def d_px(r,u,xi):       #Initial Function
    x = lambda r,u,xi: ((r**2)+(u**2)+(xi**2))/(2*r*u)
    return x(r,u,xi)-(np.sqrt((x(r,u,xi)**2)-1))

def d_rho0(r, h, d_rho00=rho00_c): #density piecewise function
    condlist = [r <= R(h), (r > R(h)) & (r <= (R(h)+d(h))), r > (R(h)+d(h))]
    funclist = [lambda r,h,d_rho00: rho00*np.exp(-r/h), lambda r,h,d_rho00: rho00*np.exp(-R/h)*(1-((r-R)/d)), lambda r,h,d_rho00: 0]
    return np.piecewise(r, h, d_rho00, condlist, funclist)

def d_durho0(r, h, d_rho00=rho00_c): #partial derivative of rho(u,xi)
    condlist = [r <= R(h), (r > R(h)) & (r <= (R(h)+d(h))), r > (R(h)+d(h))]
    funclist = [lambda r,h,d_rho00: -(1/h)*d_rho00*np.exp(-r/h), lambda r,h,d_rho00: -(1/d)*d_rho00*np.exp(-R/h), lambda r,h,d_rho00: 0]
    return np.piecewise(r, h, d_rho00, condlist, funclist)
    #Thinks that funclist is a float??

#Disk Density Distribution
def d_rho_rz(r,z,h,d_rho00):
    return d_rho0(r, h, d_rho00)*(np.power((np.cosh(z/z0)), (-2)))
def d_drho_rz(r,z,h,d_rho00):
    return d_durho0(r, h, d_rho00)*(np.power(np.cosh(z/z0), -2))

#Disk Density Distribution (3D)

def d_K(r,u,xi): #Complete Elliptic Integral
    return ss.ellipk(d_px(r,u,xi)) - ss.ellipe(d_px(r,u,xi))

def d_innerfunc(z,r,u,h,d_rho00):  #Inner Function (3D)
    return u*d_drho_rz(u, z, h, d_rho00)*(2*d_K(r,u,z))/(np.pi*np.sqrt(r*u*d_px(r,u,z)))

def d_innerintegral(u,r,h,d_rho00): #Integrate Function
    return si.quad(d_innerfunc, 0, np.inf, args=(r,u,h,d_rho00))[0]

def d_outerintegral(r,h,d_rho00): #Integrate Outer Function
    return si.quad(d_innerintegral, 0, np.inf, args=(r,h,d_rho00))[0]

def d_Mdblintrho(r,h,d_rho00):
    rho_rz_r = lambda z,r: d_rho_rz(r,z,h,d_rho00)*r
    d_Mintrho = lambda r,h,d_rho00: si.quad(rho_rz_r, -125, 125, args=(r,h,d_rho00))[0]
    return si.quad(d_Mintrho,0,np.inf)[0]

def d_F(r,pref): #multiplying by upsylon
    pref = lambda r: epsdisk*(L0/d_Mdblintrho(r,h=h_c,d_rho00=rho00_c))
    return 4*np.pi*G*d_outerintegral(r,h=h_c,d_rho00=rho00_c)*pref(r,h=h_c,d_rho00=rho00_c)
d_Fv = np.vectorize(d_F)

def d_v(r,pref,save=False,load=False,**kwargs): #velocity
    if save:
        a = np.sqrt(-r*d_Fv(r,pref))
        a[np.isnan(a)] = 0
        savedata(r,a,'disk','pref'+str(pref),**kwargs)
        return a
    elif load:
        y = loaddata('disk','pref'+str(pref),**kwargs)[1]
        x = loaddata('disk','pref'+str(pref),**kwargs)[0]
        a = inter.InterpolatedUnivariateSpline(x,y,k=3) #k is the order of the polynomial
        return a(r)
    else:
        return np.sqrt(-r*d_Fv(r,pref))

################################
############ Total #############
################################
def v(r,M=Mbh_def,n=n_c): 
    if save:
        a = np.sqrt(np.sqrt(h_v(r)**2+d_v(r)*d_v(r)+bh_v(r,M)**2+b_v(r,n)**2))
        savedata(r,a,'total','Mbh'+str(M)+'n'+str(n)+'n'+str('PLACEHOLDERx2'),**kwargs)
        return a
    elif load:
        return loaddata('total','Mbh'+str(M)+'n'+str(n)+'n'+str('PLACEHOLDERx2'),**kwargs)
    else:
        return np.sqrt(h_v(r)**2+d_v(r)*d_v(r)+bh_v(r,M)**2+b_v(r,n)**2)