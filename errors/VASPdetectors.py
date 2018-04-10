import subprocess, os
from HighThroughput.manage.calculation import getResults,updateResults
from HighThroughput.modules.VASP import gather
import numpy as np

def test(calc):
    print('SEARCHING FOR ERRORS')
    det = int(subprocess.Popen('grep WAAAAAAAAAGH tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if det > 0:
        return True
    else:
        return False

def maxSteps(calc):
    #Slow, bad or no convergence
    nsteps = subprocess.Popen('grep -e "  .*  .*  .*  .*  .*  .*" OSZICAR | grep : | grep -v vasp | awk \'{print $2}\' | tail -n 1',shell=True,stdout=subprocess.PIPE).communicate()[0].strip()
    
    if nsteps.isdigit():
        nsteps = int(nsteps)
    else:
        return False
    if 'NELM' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['NELM'] = 60
    
    print(str(nsteps) + ' performed of ' + str(calc['settings']['INCAR']['NELM']) + ' allowed steps')

    if nsteps == int(calc['settings']['INCAR']['NELM']):
        return True
    else:
        return False

def gradNotOrth(calc):
    #Corrupted CHGCAR, POTCAR or optimizer/lib issue in VASP
    detected = int(subprocess.Popen('fgrep "EDWAV: internal error, the gradient is not orthogonal" tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if detected > 0:
        return True
    else:
        return False

def planeWaveCoeff(calc):
    #Grid/basis set/whatnot changed
    detected = int(subprocess.Popen('fgrep "ERROR: while reading WAVECAR, plane wave coefficients changed" tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if detected > 0:
        return True
    else:
        return False

def ZPOTRF(calc):
    #Grid/basis set/whatnot changed
    detected = int(subprocess.Popen('fgrep "LAPACK: Routine ZPOTRF failed!" tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if detected > 0:
        return True
    else:
        return False


def PSSYEVX(calc):
    #Grid/basis set/whatnot changed
    detected = int(subprocess.Popen('fgrep "ERROR in subspace rotation PSSYEVX: not enough eigenvalues found" tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if detected > 0:
        return True
    else:
        return False

def energyMissing():
    #Energy cannot be extracted from OUTCAR
    energy = int(subprocess.Popen('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $8 }\'',shell=True,stdout=subprocess.PIPE).communicate()[0]).strip()
    if energy == '' or not 'energy' in locals():
        return True
    else:
        return False

def chgMissing():
    if not os.path.isfile('CHGCAR') or not os.path.isfile('CHG'):
        return True
    else:
        return False
    
def notConverged(calc):
    presults = getResults(calc['parent'])
    error = False
    if 'convergence' not in presults.keys():
        return False
    else:
        #"convergence": [["Ehull", ["K", 0.01, [], 0]]] format, could add more than two els to each tuple to determine how to increase the settings and so on
        new = []
        for propset in presults['convergence']:
            print('propset',propset, len(propset))
            total = len(propset)
            prop = propset[0]
            pnew = (prop,)
            for i in range(1,total):
                (crit,cond,current,converged) = propset[i]
                if converged == 1:
                    pnew += tuple(propset[i])
                    continue;
                print('Checking ' + prop + ' convergence ' + ' with respect to ' + crit + '.')


                newval = gather({ prop  : ''})[prop]
                
                current.append(newval)
                
                if len(current) == 1:
                    error = True
                else:
                    delta = np.abs(current[-1] - current[-2])

                    if delta > cond:
                        print('Not converged. Remaining error of ' + str(delta) + ' on ' + prop + '.')
                        error = True
                    else:
                        print('Property ' + prop + ' is converged up to ' + str(delta) + '.')
                        if crit == 'K':
                            presults['settingsmod']['KPOINTS']['K'] = ' '.join([str(int(x) - 2) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')])
                        elif crit == 'ENCUT':
                            presults['settingsmod']['INCAR']['ENCUT'] -= 100
                        converged = 1
                pnew += ((crit,cond,current,converged),)
            print('pnew', pnew)
            new.append(pnew)
    print('new',new)
    presults['convergence'] = new
    updateResults(presults,calc['parent'])               
    return error