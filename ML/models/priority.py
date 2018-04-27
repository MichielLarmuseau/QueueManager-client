# -*- coding: utf-8 -*-
import pandas as pd
from HighThroughput.manage.calculation import setPriority
from HighThroughput.ML.features.database import getFile,getResults
from HighThroughput.ML.features.elements import addElemental
from HighThroughput.utils.generic import getClass

def calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    
    allmats = getFile(queue,0)
    
    if target in ['Ehull','E0','Eatom','Epure']:
        materials = getResults(queue,stat,list(target))
    
    elref = set(['atomicnumber','mass','Ecoh','n','s','p','d','Ecoh','V','r','EN','EA','IP'])
    
    elfeatures = set(features).intersection(elref)
    
    allmats = addElemental(allmats,elfeatures)
    materials = addElemental(materials,elfeatures)
    

    mclass = getClass(modelClass)

    model = mclass()
    model.fit(materials['features'],materials['target'])
    
    preds = model.predict(allmats['features'])
    
    priority = - 100*preds.astype(int)
    output = pd.DataFrame({'file' : allmats['file'], 'priority' : priority})
    return output
    
def updateMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features):
    priorities = calcMLPriority(queue,stat,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target,features)
    
    for p in priorities:
        setPriority('NEEDS TO BE CALCID NOT FILE',p['priority'])
    
    