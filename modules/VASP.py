from HighThroughput.communication.mysql import *
from HighThroughput.utils.generic import  *
from HighThroughput.io.VASP import *
import os,time,shutil,subprocess,linecache, threading, math 
#cleanup function

def inherit2(stat,qdir,cfile):
    if int(stat) < 2:
        inputfile = os.path.join(qdir, 'import', str(cfile) + '.vasp')
    else:
        inputfile = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(int(stat)-2), 'CONTCAR')
        density = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(int(stat)-2), 'CHGCAR')
        wavefunctions = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(int(stat)-2), 'WAVECAR')
        #if os.path.isfile('CHGCAR'):
        #    os.rename('CHGCAR','CHGCAR.prec')
        if os.path.isfile(density):
            shutil.copy(density, './CHGCAR')
        if os.path.isfile(wavefunctions):
            shutil.copy(wavefunctions, './WAVECAR')
    shutil.copy(inputfile, './POSCAR')

    return 0 

def inherit(stat,qdir,cfile):
    pstep = int(math.ceil(float(stat)/2.)) -1
    if int(stat) < 2:
        inputfile = os.path.join(qdir, 'import', str(cfile) + '.vasp')
    else:
        inputfile = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(pstep), 'CONTCAR')
        density = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(pstep), 'CHGCAR')
        wavefunctions = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(pstep), 'WAVECAR')
        #if os.path.isfile('CHGCAR'):
        #    os.rename('CHGCAR','CHGCAR.prec')
        if os.path.isfile(density):
            shutil.copy(density, './CHGCAR')
        if os.path.isfile(wavefunctions):
            shutil.copy(wavefunctions, './WAVECAR')
    shutil.copy(inputfile, './POSCAR')

    return 0

def abort(cinfo,delay=0,mode = 0):
    import HighThroughput.manage.calculation as manage
    # either switch between electronic and ionic or auto based on ibrion is possible
    #for now 0 is electronic stop, 1 ionic
    time.sleep(delay)
    f = open('STOPCAR','w')
    if mode ==0:
        f.write('LABORT=.TRUE.')
    else:
        f.write('LSTOP=.TRUE.')
    f.close()
    open('aborted', 'a').close()
    manage.restart(cinfo['id'])
    psettings = manage.getSettings(manage.calcid)
    if 'continue' in psettings.keys():
        psettings['continue'] = str(int(psettings['continue']) + 1)
    else:
        psettings['continue'] = '1'
    manage.modify({'settings' : psettings, 'id' : manage.calcid})
    return 0


def checkpointStart(cinfo,early=4400):
    walltime = int(os.getenv('PBS_WALLTIME'))
    thread = threading.Thread(target=abort,args=(cinfo,walltime-early,0))
    thread.daemon = True
    thread.start()
    return 0

def cont(calc):
    import HighThroughput.manage.calculation as manage
    baks = 0
    bako = 0
    bakx = 0
    bakt = 0

    for file in os.listdir(os.curdir):
        if os.path.isfile(file) and file[0:10] == 'POSCAR.bak':
            baks += 1
        if os.path.isfile(file) and file[0:10] == 'OUTCAR.bak':
            bako += 1
        if os.path.isfile(file) and file[0:11] == 'XDATCAR.bak':
            bakx += 1
        if os.path.isfile(file) and file[0:11] == 'tempout.bak':
            bakt += 1

    if os.path.isfile('CONTCAR') and os.stat('CONTCAR').st_size > 0:
        os.rename('POSCAR','POSCAR.bak' + str(baks))
        os.rename('CONTCAR','POSCAR')
    if os.path.isfile('OUTCAR') and os.stat('OUTCAR').st_size > 0:
        os.rename('OUTCAR','OUTCAR.bak' + str(bako))
    if os.path.isfile('XDATCAR') and os.stat('XDATCAR').st_size > 0:
        os.rename('XDATCAR','XDATCAR.bak' + str(bakx))
    if os.path.isfile('tempout') and os.stat('tempout').st_size > 0:
        os.rename('tempout','tempout.bak' + str(bakt))
    psettings = manage.getSettings(calc['parent'])
    if 'continued' not in psettings.keys():
        psettings['continued'] = 1
    else:
        psettings['continued'] += 1
    manage.updateSettings(psettings, calc['parent'])
    return calc

def finish():
    #end and readresults, readsettings too possibly, makecif populateresults and convert E/atom etc possibilities of using tables for chemical potentials
    #DOS and bandstructure options here too or in seperate postprocess func
    #Incorporate HTfinish, other httools should go somewhere too
    print('')
    return 0

def initialize(settings,hard = ''):
    #print 'write incar kpoints potcar, make directory?'
    #inherit()
    writeSettings(settings)
    poscar = open('./POSCAR','r')
    lines = poscar.readlines()
    elements = lines[5][:-1].strip()
    execute('POTgen' + str(hard)  + ' ' + str(elements))
    return 0

def prepare(settings):
    #preparing any configs, can turn on SP and SO here too
    parallelSetup(settings)
    #print 'settings should be modified anyways'
    return settings

def getIBZKPT():
    curdir = os.getcwd()
    if os.path.isdir(os.path.join(curdir,'genIBZKPT')):
        os.system('rm -rf ' + os.path.join(curdir,'genIBZKPT'))

    mkdir('genIBZKPT')
    os.chdir(os.path.join(curdir,'genIBZKPT'))
    shutil.copy2('../POSCAR','./POSCAR')
    shutil.copy2('../POTCAR','./POTCAR')
    shutil.copy2('../INCAR','./INCAR')
    shutil.copy2('../KPOINTS','./KPOINTS')
    genIBZKPT = subprocess.Popen(vasp,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    i = 0
    while(not os.path.isfile(os.path.join(curdir,'genIBZKPT','IBZKPT'))):
        time.sleep(1)
        i+=1
        if i == 1000:
            print('IBZKPT NOT GENERATED ERROR')
            sys.exit()
    genIBZKPT.terminate()
    f = open('IBZKPT', 'r')
    lines = f.readlines()
    f.close()
    os.chdir(curdir)
    os.system('rm -rf ' + os.path.join(curdir,'genIBZKPT'))

    return int(lines[1].strip())

def detectSP(poscar):
    poscar = open(os.path.join(poscar),'r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()
    magel = set(['O','Ni','Cr','Co','Fe','Mn','Ce','Nd','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm']);
    magnetic = False;

    for magn in magel:
        if magn in elements.split(' '):
             magnetic = True;

    return magnetic

def detectSO(poscar):
    poscar = open(os.path.join(poscar),'r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()
    relel = set(['Cs','Ba','La','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn']);

    relativistic = False;

    for rel in relel:
        if rel in elements.split(' '):
             relativistic = True;

    return relativistic

def run(ratio = 1,cwd = None):
    #could move hybrid to parallel setup
    if cwd == None:
        cwd = os.getcwd();
    nodes = getNodeInfo()

    #cores = mysql_query('SELECT `cores` FROM `clusters` WHERE `name` = ' + str(os.getenv('VSC_INSTITUTE_CLUSTER')))
    hybrid = str(min(nodes.values())/int(ratio))
    return execute('mympirun -h ' + hybrid + ' --output ' + cwd + '/tempout' + vasp)
    

def readSettings(settings):
    settings['INCAR'] = readINCAR()
    settings['KPOINTS'] = readKPOINTS()
    POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
    settings['POTCAR'] = POTCAR_version.strip().replace('\n',', ')
    #read/writePOTCAR would be useful
    return settings

def parallelSetup(settings):
    numKP = getIBZKPT()
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    kpar = min(len(nodes),numKP)
    settings['INCAR']['NCORE'] = ncore
    if 'LHFCALC' in settings['INCAR'].keys():
        if settings['INCAR']['LHFCALC'] == '.TRUE.':
            settings['INCAR']['NCORE'] = 1

    #unsure about HFc
    if 'ALGO' in settings['INCAR'].keys():
        if settings['INCAR']['ALGO'][0:2] == 'GW' or settings['INCAR']['ALGO'] == 'ACFDT' or settings['INCAR']['ALGO'] == 'HFc':
            settings['INCAR']['NCORE'] = 1

    settings['INCAR']['KPAR'] = kpar
    return settings

def setupDir(settings):
    #print 'can make potcar and writesettings'
    #inherit too
    writeSettings(settings)
    return 0

def writeSettings(settings):
    writeKPOINTS(settings['KPOINTS'])
    writeINCAR(settings['INCAR'])
    return 0

def gather(results):
    for key in results:
        if key[0:2] == 'E0':
            results[key] = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $8 }\''))
    return results

def converge(criteria):
    for key in criteria:
        print('test')
        #property to converge, setting and limit, check dict, 1 by 1, do 1 convergence at a time, store in parent converge : { kp : [previous energies], ecut : []}
        # check if key in dictionary if not add key to dict, else add energy to list, create delta array, check if converged
        # if converged return True else False or the failed property? if converged, HT.end else HT.restart/rollback if not True increaseSettings(property)