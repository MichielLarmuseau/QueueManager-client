import os,math
from HighThroughput.manage.calculation import getResults,updateResults,getSettings
import numpy as np

def test(calc):
    #Dummy
    print('This is a bugfix.')
    return True

def rmWAVECAR(calc):
    #2: CHGCAR more reliable so clear WAVECAR
    if os.path.isfile('WAVECAR'):
        open('WAVECAR', 'w').close() 
        
    if os.path.isfile('WAVECAR.gz'):
        open('WAVECAR.gz', 'w').close()
        
    return True

def rmCHGCAR(calc):
    #7: In case of corrupted density
    if os.path.isfile('CHGCAR'):
        open('CHGCAR', 'w').close()
        
    if os.path.isfile('CHGCAR.gz'):
        open('CHGCAR.gz', 'w').close()
        
    return True

def algoSwitch(calc):
    #3: Switch between All/Damped Normal/Fast
    if 'ALGO' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['ALGO'] = 'Fast'
    elif  calc['settings']['INCAR']['ALGO'][0] == 'N':
        calc['settings']['INCAR']['ALGO'] = 'Normal'
    elif calc['settings']['INCAR']['ALGO'][0] == 'D':
        calc['settings']['INCAR']['ALGO'] = 'A'
    elif calc['settings']['INCAR']['ALGO'][0] == 'A':
        calc['settings']['INCAR']['ALGO'] = 'D'
    return True

def halveStep(calc):
    #4: bit much for multiple times
    if 'TIME' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['TIME'] = math.ceil(float(calc['settings']['INCAR']['TIME'])*100.0/2.0)/100.0
    elif 'POTIM' in calc['settings']['INCAR']:
        calc['settings']['INCAR']['POTIM'] = math.ceil(float(calc['settings']['INCAR']['POTIM'])*100.0/2.0)/100.0
    return True

def doubleStep(calc):
    #5: bit much for multiple times
    if 'TIME' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['TIME'] = float(calc['settings']['INCAR']['TIME'])*2.0
    elif 'POTIM' in calc['settings']['INCAR']:
        calc['settings']['INCAR']['POTIM'] = float(calc['settings']['INCAR']['POTIM'])*2.0
    return True

def preconv(calc):
    #8: Preconverge calculation with another algorithm.
    preconvAlgo = {'A' : 'N', 'D' : 'N'}
    calc['settings']['INCAR']['ALGOb'] = calc['settings']['INCAR']['ALGO']
    calc['settings']['INCAR']['ALGO'] = preconvAlgo[calc['settings']['INCAR']['ALGO'][0]]
    calc['settings']['INCAR']['NELMb'] = calc['settings']['INCAR']['NELM'] 
    calc['settings']['INCAR']['NELM'] = '8'
    return True

def restorePreconv(calc):
    #9: Restore the original settings before preconvergence.
    if os.path.isfile('CHGCAR.prec'):
        if os.stat('CHGCAR.prec').st_size > 0:
            os.rename('CHGCAR.prec','CHGCAR')
    if 'ALGOb' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['ALGO'] = calc['settings']['INCAR']['ALGOb'] 
        del calc['settings']['INCAR']['ALGOb'] 
    if 'NELMb' in calc['settings']['INCAR'].keys(): 
        calc['settings']['INCAR']['NELM'] = calc['settings']['INCAR']['NELMb']
        del calc['settings']['INCAR']['NELMb']
    return True

def startWAVECAR(calc):
    #10 Ensure a preconverged WAVECAR is used for the new coefficients and the density.
    calc['settings']['INCAR']['ISTART'] = "1"
    calc['settings']['INCAR']['ICHARG'] = "0"    
    return True

def startCHGCAR(calc):
    calc['settings']['INCAR']['ISTART'] = "0"
    calc['settings']['INCAR']['ICHARG'] = "1"
    return True


def converge(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = {}
        
    for propset in presults['convergence']:
        total = len(propset)
        prop = propset[0]
        for i in range(1,total):
            (crit,cond,current,converged) = propset[i]
            if converged == 1:
                continue;
            elif crit == 'K':
                if 'KPOINTS' not in presults['settingsmod'].keys():
                    presults['settingsmod']['KPOINTS'] = {}
                if 'K' not in presults['settingsmod']['KPOINTS'].keys():
                    presults['settingsmod']['KPOINTS']['K'] = '2 2 2'
                else:
                    presults['settingsmod']['KPOINTS']['K'] = ' '.join([str(int(x) + 2) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')])
            #curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
           #curmod = [int(x) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')]
             #   calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
                break;
            elif crit == 'ENCUT':
                if 'INCAR' not in presults['settingsmod'].keys():
                    presults['settingsmod']['INCAR'] = {}
                if 'ENCUT' not in presults['settingsmod']['INCAR']:
                    presults['settingsmod']['INCAR']['ENCUT'] = 100
                else:
                    presults['settingsmod']['INCAR']['ENCUT'] += 100
              #  calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + presults['settingsmod']['INCAR']['ENCUT']
                break;
    updateResults(presults,calc['parent'])
    return True