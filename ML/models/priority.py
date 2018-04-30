# -*- coding: utf-8 -*-
import pandas as pd
from HighThroughput.manage.calculation import setPriority
from HighThroughput.ML.features.database import getFile,getResults
from HighThroughput.ML.features.elements import addElemental
from HighThroughput.utils.generic import getClass
import sklearn.gaussian_process as gp
from scipy.stats import norm
from gpflowopt.Domain import ContinuousParameter
from gpflowopt.design import LatinHyperCube
import numpy

def calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    
    allmats = getFile(queue,0)
    
    if target in ['Ehull','E0','Eatom','Epure']:
        materials = getResults(queue,stat,list(target))
    
    elref = set(['atomicnumber','mass','Ecoh','n','s','p','d','Ecoh','V','r','EN','EA','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)
    materials = addElemental(materials,elfeatures)
            
    kernel = gp.kernels.ConstantKernel()*gp.kernels.Matern(nu=5/2)+gp.kernels.WhiteKernel()
    model  = gp.GaussianProcessRegressor(kernel=kernel,
                                alpha=1e-5,
                                n_restarts_optimizer=10,
                                normalize_y=True)
#    mclass = getClass(modelClass)

#    model = mclass()

    model.fit(materials['features'],materials['target'])
    
    mu, sigma = model.predict(allmats['features'], return_std=True)
    
    rank =  norm.cdf((0.05-mu)/sigma).argsort() #argsort works in ascending order, higher rank means higher priority
    
    priority = np.zeros_like(rank)
    
    for count, rnk in enumerate(rank):
        priority[rnk] = count #the higher the rank, the more important the material and thus higher priority
    
    output = pd.DataFrame({'file' : allmats['file'], 'priority' : priority})
    return output

def calcInitialPriority(queue, features, N_init=50):
    allmats = getFile(queue,0)
    
    elref = set(['atomicnumber','mass','Ecoh','n','s','p','d','Ecoh','V','r','EN','EA','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)
    
    domain = gpflowopt.domain.ContinuousParameter('x1', min(X[:,0]), max(X[:,0]))

    for i in np.arange(1, X.shape[1]):
        domain += gpflowopt.domain.ContinuousParameter('x'+str(i+1), min(X[:,i]), max(X[:,i]))

    design = LatinHyperCube(N_init, domain)
    
    X0 = design.generate()
    
    indices = []
    
    for x0 in X0:
        for j in range(allmats.shape[0]):
            index_new = np.sum(np.abs(X-x0),axis=1).argsort()[j]
            if index_new not in indices:
                indices.append(index_new)
                break
    
    priority = np.zeros(allmat.shape[0])
    
    for index in indices:
        priority[index]=1
    
    output = pd.DataFrame({'file' : allmats['file'], 'priority' : priority})

    return output

def updateMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    priorities = calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features)
    
    for p in priorities:
        setPriority('NEEDS TO BE CALCID NOT FILE',p['priority'])
    
def setMLPriority(queue,stat, features):
    priorities = calcInitialPriority(queue, features)
    
    for p in priorities:
        setPriority('NEEDS TO BE CALCID NOT FILE',p['priority'])    
