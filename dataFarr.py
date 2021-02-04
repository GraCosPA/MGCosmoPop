import numpy as np
import h5py
import os


###############################################
#  GLOBAL VARIABLES
###############################################


dirName  = os.path.join(os.path.dirname(os.path.abspath(__file__)))
dataPath=os.path.join(dirName, 'data')

###############################################
#  LOADING DATA
###############################################




def load_mock_data():
    with h5py.File(os.path.join(dataPath,'observations.h5'), 'r') as phi: #observations.h5 has to be in the same folder as this code
   
        m1det_samples = np.array(phi['posteriors']['m1det'])# m1
        m2det_samples = np.array(phi['posteriors']['m2det']) # m2
        dl_samples = np.array(phi['posteriors']['dl'])*10**3 # dLm distance is given in Gpc in the .h5
        #theta_samples = np.array(phi['posteriors']['theta']) [:10,:100] # theta
        # Farr et al.'s simulations: our "observations"
        
    return np.array([m1det_samples, m2det_samples, dl_samples])



def load_injections_data():
    with h5py.File(os.path.join(dataPath,'selected.h5'), 'r') as f:
        m1_sel = np.array(f['m1det'])
        m2_sel = np.array(f['m2det'])
        dl_sel = np.array(f['dl'])*10**3
        weights_sel = np.array(f['wt'])
        N_gen = f.attrs['N_gen']
        
    return np.array([m1_sel, m2_sel, dl_sel]), weights_sel , N_gen





