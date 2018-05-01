# -*- coding: utf-8 -*-
import pandas as pd
from HighThroughput.manage.calculation import setPriority
from HighThroughput.ML.features.database import getFile,getResults
from HighThroughput.ML.features.elements import addElemental
from HighThroughput.utils.generic import getClass
import sklearn.gaussian_process as gp
from scipy.stats import norm
from sklearn.decomposition import PCA
import numpy as np
from gpflowopt.domain import ContinuousParameter
from gpflowopt.design import LatinHyperCube

def calcInitialMLPriority(queue, features, N_init = 50):
    
    stable_limit = 0.05 #Stable limit is fixed
    
    allmats = getFile(queue,0)
    
    elref = set(['mass','Ecoh','EN','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)
    materials = addElemental(materials,elfeatures)

    #apply pca to all materials
    X = pca.fit_transform(allmats['features'])
    
    #create a domain to generate initial sampling plan
    domain = gpflowopt.domain.ContinuousParameter('x1', min(X[:,0]), max(X[:,0]))

    for i in np.arange(1, X.shape[1]):
        domain += gpflowopt.domain.ContinuousParameter('x'+str(i+1), min(X[:,i]), max(X[:,i]))

    design = LatinHyperCube(N_init, domain)
    
    #X0 is the intial sampling plan in continuous space
    X0 = design.generate()
    
    #indices will contain the indices of the materials to sample initially
    indices = []
    
    #look for the indices of the materials that lay closest to the sample points in continuous space
    for x0 in X0:
        for j in range(X.shape[0]):
            index_new = np.linalg.norm(X-x0,axis=1).argsort()[j]
            if index_new not in indices:
                indices.append(index_new)
                break
    
    #create priority based on obtained indices
    priority = np.zeros_like(X.shape[0])
    
    #priority is put equal to X.shape to assure preference over the updated priorities based on ML
    for index in indices:
        priority[index] = X.shape[0]
    
    #priority can be computed directly, without "indices", but "indices" might be useful for debugging
        
    output = pd.DataFrame({'file' : allmats['file'], 'priority' : priority})
    return output

def calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    
    stable_limit = 0.05 #Stable limit is fixed
    
    allmats = getFile(queue,0)
    
    if target in ['Ehull','E0','Eatom','Epure']:
        materials = getResults(queue,stat,list(target))
    
    elref = set(['mass','Ecoh','EN','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)
    materials = addElemental(materials,elfeatures)
    
    #apply pca to all materials and to train set
    pca = PCA(n_components=4)
    
    X_all = pca.fit_transform(allmats['features'])

    X_train = pca.transform(materials['features'])
    
    #initialize kernel and GP
    kernel = gp.kernels.ConstantKernel()*gp.kernels.Matern()+gp.kernels.WhiteKernel()
    model  = gp.GaussianProcessRegressor(kernel=kernel,
                                alpha=1e-5,
                                n_restarts_optimizer=10,
                                normalize_y=True)
    #fit model
    model.fit(X_train,materials['target'])
    
    #get predictions and uncertainties
    mu, sigma = model.predict(X_all, return_std=True)

    #get rank, the higher the better
    rank = norm.cdf((stable_limit-mu)/sigma).argsort() 
    
    #create priorities based on rank 
    priority = np.zeros_like(rank)
    
    #The higher in the ranking the higher the prioirity should be 
    for ind, rnk in enumerate(rank):
        priority[rnk] = ind 
    
    output = pd.DataFrame({'file' : allmats['file'], 'priority' : priority})
    return output

def updateMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    priorities = calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features)
    
    for p in priorities:
        setPriority('NEEDS TO BE CALCID NOT FILE',p['priority'])

def setMLPriority(queue, features):
    priorities = calcInitialMLPriority(queue, features)
    
    for p in priorities:
        setPriority('NEEDS TO BE CALCID NOT FILE',p['priority'])
    
