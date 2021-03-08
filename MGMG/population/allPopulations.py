#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 16:31:45 2021

@author: Michi
"""
import numpy as np
#import cosmo
from copy import deepcopy

# Logic for dN/dtheta with multiple populations (e.g. astro-ph BHs, primordial BHs, ... )


class AllPopulations(object):
    
    
    def __init__(self, cosmo):
        
        self.cosmo = cosmo
        self._initialize(cosmo)
        self.nPops=0
    
    
    def add_pop(self, population):
        print('Adding population of type %s' %population.__class__.__name__)
        print('%s parameters: %s' %( population.n_params, str(population.params) ) )
        self._pops.append(population)
        self._allNParams.append(population.n_params)
        self.params += population.params
        self.baseValues.update(population.baseValues)
        self.n_params += population.n_params
        self.names.update(population.names)
        self.nPops+=1
        print('New parameter list: %s. Total %s params' %(str(self.params),self.n_params  ) )
        assert self.n_params == len(self.params)
    
    
    def _initialize(self, cosmo):
        print('Setting cosmology.')
        self._pops = []
        self._allNParams = []
        self.params = deepcopy(self.cosmo.params)
        self.baseValues = deepcopy(self.cosmo.baseValues)
        self.n_params = len(self.params)
        self.names = deepcopy(self.cosmo.names)
        print('%s parameters: %s' %( self.n_params, str(self.params) ) )
    
    
    #########################################################################
    # Differential Rate
    
    def log_dN_dm1dm2dz(self, m1, m2, z, chiEff, Tobs, Lambda):
        
        LambdaCosmo, LambdaAllPop = self._split_params(Lambda)
        
        logN = np.log(Tobs)
        logN -= np.log1p(z) # differential of time between source and detector frame
        H0, Om0, w0 = self.cosmo._get_values(LambdaCosmo, ['H0', 'Om', 'w0'])
        logN += self.cosmo.log_dV_dz(z, H0, Om0, w0)
        
        prev=0
        for i,pop in enumerate(self._pops):
            LambdaPop = LambdaAllPop[prev:prev+self._allNParams[i]]
            logN += pop.log_dR_dm1dm2(m1, m2, z, chiEff, LambdaPop)
            prev=self._allNParams[i]
        return logN
    
    
    def log_dN_dm1zdm2zddL(self, m1, m2, z, chiEff, Tobs, Lambda):
        LambdaCosmo, LambdaAllPop = self._split_params(Lambda)
        H0, Om0, w0, Xi0, n = self.cosmo._get_values(LambdaCosmo, ['H0', 'Om', 'w0', 'Xi0', 'n'])
        return self.log_dN_dm1dm2dz(m1, m2, z, chiEff, Tobs, Lambda)-self._log_dMsourcedMdet(z) - self.cosmo.log_ddL_dz(z, H0, Om0, w0, Xi0, n )
    
    
    #########################################################################
    # Sampling 
    
    
    def sample(self, nSamples, zmax, Lambda,):
        '''
        Returns samples m1, m2, z from all the populations. 
        The sampling assumes that the redshift and mass dependence 
        in each population factorize!
        

        Parameters
        ----------
        nSamples : int
            number of samples required.
        zmax : float
            max redsift for sampling.
        Lambda : array
            all coso+astroph parameters.

        Returns
        -------
        allSamples : arrray nSamples x nPopulations x 2
            DESCRIPTION.

        '''
        allSamples = np.empty( (nSamples, self.nPops, 3) )
        
        redshiftSamples = self._sample_redshift( nSamples, zmax, Lambda,)
        massSamples = self._sample_masses( nSamples, Lambda,)
        
        allSamples[:,:, 0] = massSamples[:,:,0]
        allSamples[:,:, 1] = massSamples[:,:,1]
        allSamples[:,:, 2] = redshiftSamples
        
        return allSamples
    
    
    def _sample_spins(self, nSamples, Lambda,):
        pass
    
    
    def _sample_masses(self, nSamples, Lambda,):
        allsamples = np.empty( (nSamples, self.nPops, 2) )
        LambdaCosmo, LambdaAllPop = self._split_params(Lambda)
        #H0, Om0, w0 = self.cosmo._get_values(LambdaCosmo, ['H0', 'Om', 'w0'])
        prev=0
        for i,pop in enumerate(self._pops):
            LambdaPop = LambdaAllPop[prev:prev+self._allNParams[i]]
            #print('LambdaPop: %s' %str(LambdaPop))
            lambdaBBHrate, lambdaBBHmass, lambdaBBHspin = pop._split_lambdas(LambdaPop)
            #print('lambdaBBHmass: %s' %str(lambdaBBHmass))
            m1s, m2s =  pop.massDist.sample(nSamples, lambdaBBHmass)
            
            allsamples[:, i, 0] = m1s
            allsamples[:, i, 1] = m2s

        return allsamples
    
    
    def _sample_redshift(self, nSamples, zmax, Lambda,):
        '''
        Returns samples from the redshift distribution of all populations. 
        
        For each population, the redshift distribution id given by
        dN/dVdt * dV/dz /(1+z)

        '''
        allsamples = np.empty( (nSamples, self.nPops) )
        
        LambdaCosmo, LambdaAllPop = self._split_params(Lambda)
        H0, Om0, w0 = self.cosmo._get_values(LambdaCosmo, ['H0', 'Om', 'w0'])
        prev=0
        for i,pop in enumerate(self._pops):
            LambdaPop = LambdaAllPop[prev:prev+self._allNParams[i]]
            lambdaBBHrate, lambdaBBHmass, lambdaBBHspin = pop._split_lambdas(LambdaPop)
            
            zpdf = lambda z: np.exp(pop.rateEvol.log_dNdVdt(z, lambdaBBHrate)+ self.cosmo.log_dV_dz(z, H0, Om0, w0)-np.log1p(z))
            
            allsamples[:, i] = self._sample_pdf(nSamples, zpdf, 0., zmax)
        return allsamples
        
    
    def _sample_pdf(self, nSamples, pdf, lower, upper):
        res = 100000
        x = np.linspace(lower, upper, res)
        cdf = np.cumsum(pdf(x))
        cdf = cdf / cdf[-1]
        return np.interp(np.random.uniform(size=nSamples), cdf, x)
    
    
    
    def _log_dMsourcedMdet(self, z):
        return 2*np.log1p(z)
    
    
    #########################################################################
    # Logic for getting and setting parameters
    
    
    #def get_baseValue(self, param):
    #    if param in self.cosmo.params:
    #        return self.cosmo.baseValues[param]
    #    else:
    #        for pop in self._pops:
    #            if param in pop.params:
    #                return pop.baseValues[param]
    
    def _split_params(self, Lambda):
        '''
        Lambda is list of all parameters.
        Splits between cosmological and population parameters
        '''
        LambdaCosmo = Lambda[:self.cosmo.n_params]
        LambdaAllPop = Lambda[self.cosmo.n_params:]
        return LambdaCosmo, LambdaAllPop
    
    
    def _split_thetas(self, theta):
        if self.spinDist.__class__.__name__ =='DummySpinDist':
            m1, m2, z = theta
            theta_spin = None
        else:
            m1, m2, z, chi = theta
            theta_spin = chi
        theta_rate = z
        theta_mass = m1, m2
        return  theta_rate, theta_mass, theta_spin
    
    
    def get_base_values(self, params):
        allVals=[]
        for param in self.params:
                if param in params:
                    allVals.append(self.baseValues[param])
        return allVals
    
    
    def get_labels(self, params):
        allVals=[]
        for param in self.params:
                if param in params:
                    allVals.append(self.names[param])
        return allVals   
     
    
    def get_fixed_values(self, params_inference):
        allVals={}
        for i,param in enumerate(self.params):
            if param not in params_inference:
                allVals[param]=self.baseValues[param]
        return allVals
        
    
    def get_Lambda(self, Lambda_test, params_inference ):
        allVals=[]
        for i,param in enumerate(self.params):
            if param in params_inference:
                if np.isscalar(Lambda_test):
                    allVals.append(Lambda_test)
                else: allVals.append(Lambda_test[params_inference.index(param)])
            else: allVals.append(self.baseValues[param])
        return allVals
    
    
    def _set_values(self, values_dict):
        for key, value in values_dict.items():
            print('Setting value of %s to %s in %s' %(key, value, self.__class__.__name__))
            self.baseValues[key] = value
        
    
    def set_values(self, values_dict):
        '''
        Set values of given parameters
        Has to go through all the components of each population ! 
        '''
        
        # update values in cosmology
        self.cosmo._set_values(values_dict)
        
        # update values in each object that forms the population
        for pop in self._pops:
            pop._set_values(values_dict)
         
        # update values also in this object
        self._set_values(values_dict)
        
        
    
    
    def check_params_order(self, params_inference):
        
        for i in range(len(params_inference)-1):
            p1=params_inference[i]
            p2 =params_inference[i+1]
            cond = self.params.index(p1)<self.params.index(p2)
            if not cond:
                raise ValueError('The order of parameters %s, %s on params_inference does not match the order of parameters in the population. Check the configuration.\nOrder of parameters in the population is %s' %( p1, p2, str(self.params)))
        
        
        
