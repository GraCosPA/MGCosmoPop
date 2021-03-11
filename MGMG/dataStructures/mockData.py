#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 13:41:18 2021

@author: Michi
"""
 
from .ABSdata import Data

import numpy as np
import astropy.units as u
import h5py
#import os

        
class GWMockData(Data):
    
    def __init__(self, fname, nObsUse=None, nSamplesUse=None, dist_unit=u.Gpc ):
        
        self.dist_unit = dist_unit
        self.m1z, self.m2z, self.dL, self.Nsamples = self._load_data(fname, nObsUse, nSamplesUse, )  
        self.Nobs=self.m1z.shape[0]
        print('We have %s observations' %self.Nobs)
        print('Number of samples: %s' %self.Nsamples )
        
        self.logNsamples = np.log(self.Nsamples)
        assert (self.m1z > 0).all()
        assert (self.m2z > 0).all()
        assert (self.dL > 0).all()
        assert(self.m2z<self.m1z).all()
        
        self.Tobs=2.5
        self.chiEff = np.zeros(self.m1z.shape)
        print('Obs time: %s' %self.Tobs )
        
    def get_theta(self):
        return np.array( [self.m1z, self.m2z, self.dL  ] )  
    
    def _load_data(self, fname, nObsUse, nSamplesUse,):
        print('Loading data...')
        
        with h5py.File(fname, 'r') as phi: #observations.h5 has to be in the same folder as this code
        
            if nObsUse is None and nSamplesUse is None:
                m1det_samples = np.array(phi['posteriors']['m1det'])
                m2det_samples = np.array(phi['posteriors']['m2det'])
                dl_samples = np.array(phi['posteriors']['dl']) # dLm distance is given in Gpc in the .h5

            elif nObsUse is not None and nSamplesUse is None:
            
                m1det_samples = np.array(phi['posteriors']['m1det'])[:nObsUse, :]# m1
                m2det_samples = np.array(phi['posteriors']['m2det'])[:nObsUse, :] # m2
                dl_samples = np.array(phi['posteriors']['dl'])[:nObsUse, :] 
            
            elif nObsUse is  None and nSamplesUse is not None:
                
                which_samples = np.random.randint(0, high=4000 , size=nSamplesUse )
                m1det_samples = np.array(phi['posteriors']['m1det'])[:, which_samples]# m1
                m2det_samples = np.array(phi['posteriors']['m2det'])[:, which_samples] # m2
                dl_samples = np.array(phi['posteriors']['dl'])[:, which_samples]
            
            elif nObsUse is not None and nSamplesUse is not None:
                
                which_samples = np.random.randint(0, high=4000 , size=nSamplesUse )
                m1det_samples = np.array(phi['posteriors']['m1det'])[:nObsUse, which_samples]# m1
                m2det_samples = np.array(phi['posteriors']['m2det'])[:nObsUse, which_samples] # m2
                dl_samples = np.array(phi['posteriors']['dl'])[:nObsUse, which_samples] 
    
        if self.dist_unit==u.Mpc:
            print('Using distances in Mpc')
            dl_samples*=1e03
        #theta =   np.array([m1det_samples, m2det_samples, dl_samples])
        return m1det_samples, m2det_samples,dl_samples, np.count_nonzero(m1det_samples, axis=-1)
      
    
    def logOrMassPrior(self):
        return np.zeros(self.m1z.shape)

    def logOrDistPrior(self):
        return np.zeros(self.dL.shape)
    



class GWMockInjectionsData(Data):
    
    def __init__(self, fname, nInjUse=None,  dist_unit=u.Gpc ):
        
        self.dist_unit=dist_unit
        self.m1z, self.m2z, self.dL, self.weights_sel, self.N_gen = self._load_data(fname, nInjUse )        
        self.logN_gen = np.log(self.N_gen)
        self.log_weights_sel = np.log(self.weights_sel)
        assert (self.m1z > 0).all()
        assert (self.m2z > 0).all()
        assert (self.dL > 0).all()
        assert(self.m2z<self.m1z).all()
        self.condition=True
        
        self.Tobs=2.5
        self.chiEff = np.zeros(self.m1z.shape)
        print('Obs time: %s' %self.Tobs )
        
        
    def get_theta(self):
        return np.array( [self.m1z, self.m2z, self.dL  ] )  
    
    def _load_data(self, fname, nInjUse,):
        print('Loading injections...')
        with h5py.File(fname, 'r') as f:
        
            if nInjUse is not None:
                m1_sel = np.array(f['m1det'])[:nInjUse]
                m2_sel = np.array(f['m2det'])[:nInjUse]
                dl_sel = np.array(f['dl'])[:nInjUse]
                weights_sel = np.array(f['wt'])[:nInjUse]
            else:
                m1_sel = np.array(f['m1det'])
                m2_sel = np.array(f['m2det'])
                dl_sel = np.array(f['dl'])
                weights_sel = np.array(f['wt'])
        
            N_gen = f.attrs['N_gen']
        if self.dist_unit==u.Mpc:
            dl_sel*=1e03
        print('Number of total injections: %s' %N_gen)
        print('Number of detected injections: %s' %weights_sel.shape[0])
        return m1_sel, m2_sel, dl_sel, weights_sel , N_gen
      
    
    def originalMassPrior(self):
        return np.ones(self.m1z.shape)

    def originalDistPrior(self):
        return np.ones(self.dL.shape)    
    
