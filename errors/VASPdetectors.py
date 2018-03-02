import subprocess, os
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
    
    print(str(nsteps) + 'performed of ' + str(calc['settings']['INCAR']['NELM']) + 'allowed steps')

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