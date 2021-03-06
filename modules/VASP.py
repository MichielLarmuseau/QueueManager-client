from HighThroughput.utils.generic import  mkdir, execute, getNodeInfo
from HighThroughput.utils.eos import EquationOfState
from HighThroughput.io.VASP import rescalePOSCAR, writeINCAR, writeKPOINTS, readINCAR, readKPOINTS
import os, time, shutil, subprocess, threading, sys, ase.io
from HighThroughput.config import vasp
import HighThroughput.manage.calculation as manage
from numpy import loadtxt, prod
from numpy.linalg import norm

#cleanup function

def inherit(calc,path,contcar=True,chgcar=True,wavecar=True,settingsmod=None,grid=False,rescale=1.0):
    #pstep = int(math.ceil(float(stat)/2.)) -1
    if path == None:
        return True
        #inputfile = os.path.join(qdir, 'import', str(cfile) + '.vasp')
    
        #qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(pstep)
    if contcar:
        contcarnames = ['CONTCAR','POSCAR' + calc['file'] + '.vasp','POSCAR' + calc['file'], calc['file'], calc['file'] + '.vasp']
        for name in contcarnames:    
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                inputfile = temp
                print('Inheriting geometry from ' + inputfile + '.')
                shutil.copy2(inputfile, './POSCAR')
                rescalePOSCAR('POSCAR',rescale)
                break;

    if chgcar:
        chgcarnames = ['CHGCAR.gz','CHGCAR','CHGCAR' + calc['file'] + '.gz','CHGCAR' + calc['file']]
        for name in chgcarnames:       
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                density = temp
                out = 'CHGCAR'
                if density[-3:] == '.gz':
                    out += '.gz'
                print('Inheriting charge density from ' + density + '.')
                shutil.copy2(density, out)
                if calc['settings']['INCAR'].get('ICHARG') == None:
                    calc['settings']['INCAR']['ICHARG'] = 1
                break;
            
    if wavecar:
        wavecarnames = ['WAVECAR.gz','WAVECAR','WAVECAR' + calc['file']+ '.gz','WAVECAR' + calc['file']]
        for name in wavecarnames:       
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                wavecar = temp
                out = 'WAVECAR'
                if wavecar[-3:] == '.gz':
                    out += '.gz'
                print('Inheriting wave functions from ' + wavecar + '.')
                shutil.copy2(wavecar, out)
                break;
    if grid:
        outcar = os.path.join(path, 'OUTCAR')
        ng = execute('grep "dimension x,y,z NGX" ' + outcar + ' | head -n 1').strip().split()
        calc['settings']['INCAR']['NGX'] = int(ng[4])
        calc['settings']['INCAR']['NGY'] = int(ng[7])
        calc['settings']['INCAR']['NGZ'] = int(ng[10])
              
    if settingsmod:
        presults = manage.getResults(calc['parent'])
        presults['settingsmod'] = settingsmod
        manage.updateResults(presults,calc['parent'])
        print('These setting mods are inherited:')
        print(presults['settingsmod'])
        if settingsmod.get('KPOINTS').get('K') != None and calc['settings'].get('KPOINTS').get('K') != None:
            curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
            curmod = [int(x) for x in settingsmod['KPOINTS']['K'].split(' ')]
            calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
            print('Calibration update to kpoints executed.')
    
        if settingsmod.get('ENCUT') != None:
            calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + settingsmod['INCAR']['ENCUT']

        #if os.path.isfile('CHGCAR'):
        #    os.rename('CHGCAR','CHGCAR.prec')
    return calc

def abort(cinfo,delay=0,mode = 0):
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
    presults = manage.getResults(calc['parent'])
    
    if 'continued' not in psettings.keys():
        psettings['continued'] = 1
    else:
        psettings['continued'] += 1


    if presults.get('settingsmod') != None:
        if presults['settingsmod'].get('KPOINTS').get('K') != None and calc['settings']['KPOINTS'].get('K') != None:
            curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
            curmod = [int(x) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')]
            calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
    
        if 'ENCUT' in presults['settingsmod'].keys():
            calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + presults['settingsmod']['INCAR']['ENCUT']
    
    manage.updateSettings(psettings, calc['parent'])
    manage.updateResults(presults, calc['parent'])

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
    global vasp
    #could move hybrid to parallel setup
    if cwd == None:
        cwd = os.getcwd();
    nodes = getNodeInfo()

    #cores = mysql_query('SELECT `cores` FROM `clusters` WHERE `name` = ' + str(os.getenv('VSC_INSTITUTE_CLUSTER')))
    hybrid = str(int(min(nodes.values())/int(ratio)))
    return execute('mympirun -h ' + hybrid + ' --output ' + cwd + '/tempout ' + vasp)
    

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

def eosPrepare(directory = None, evname = 'EOS'):
    if directory == None:
        directory = os.getcwd()
    currentdir = os.getcwd()
    os.chdir(directory)
    os.chdir('../')
    
    #Setup e-v.dat
    eos = {}
    with open(evname,'w') as eosfile:
        for i in os.listdir():
            if os.path.isdir(i) and i.replace('.','',1).isdigit():
                E = execute('grep \'energy  without entropy\'  ' + i + '/OUTCAR | tail -1 | awk \'{ print $7 }\'').strip()
                V = execute('grep vol ' + i + '/OUTCAR | tail -n 1 | awk \'{print $5}\'').strip()
                eos[i] = (E,V)
                eosfile.write(V + ' ' + E + '\n')
    
    os.chdir(currentdir)
    return eos

def eosFit(directory = None, evname = 'EOS'):
    if directory == None:
        directory = os.getcwd()
    currentdir = os.getcwd()
    os.chdir(directory)
    os.chdir('../')
    
    data = loadtxt(evname)

    eos = EquationOfState(data[:,0], data[:,1])
    v0, e0, B, BP, residuals = eos.fit()

    outfile = open(evname.replace('.eos','') + '.eosout', 'w')
    outfile.write('Equation Of State parameters - least square fit of a real Birch Murnaghan curve' + '\n' + '\n')
    outfile.write('V0 \t %.5f \t A^3 \t \t %.4f \t b^3 \n' % (v0,v0/eos.b3))
    outfile.write('E0 \t %.6f \t eV \t \t %.6f \t Ry \n' % (e0,e0/eos.Ry))
    outfile.write('B \t %.3f \t GPa \n' % (B * eos._e * 1.0e21))
    outfile.write('BP \t %.3f \n' % BP)
    outfile.write('\n')
    outfile.write('1-R^2: '+str(residuals)+'\n')
    outfile.close()

    eos.plot(filename='EOS.png',show=None)

    os.chdir(currentdir)
    return v0, e0, B, BP, residuals

def gather(results):
    for key in results:
        if key[0:2] == 'E0':
            results[key] = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\''))
            if 'atom' in key:
                poscar = open('POSCAR','r')
                lines = poscar.readlines()
        
                numberofatoms = lines[6][:-1].lstrip()
                numberofatoms = " ".join(numberofatoms.split())
                numberofatoms = sum(map(int, numberofatoms.split(' ')))/numberofatoms
                results[key] /= numberofatoms
        elif key == 'natoms':
            poscar = open('POSCAR','r')
            lines = poscar.readlines()
    
            numberofatoms = lines[6][:-1].lstrip()
            numberofatoms = " ".join(numberofatoms.split())
            numberofatoms = sum(map(int, numberofatoms.split(' ')))/numberofatoms
            results[key] = numberofatoms
        elif key == 'Ehull':
            results[key] = float(execute('HTehull ./'))
        elif key == 'Eatom':
            #to be implemented
            results[key] = float(execute('HTehull ./'))   
        elif key == 'Epure':
            #to be implemented
            results[key] = float(execute('HTehull ./'))
        elif key == 'cellparams':
            crystal = ase.io.read('CONTCAR')
            results[key] = list(crystal.get_cell_lengths_and_angles())
        elif key == 'volume':
            results[key] = float(execute('grep vol OUTCAR | tail -n 1 | awk \'{print $5}\''))
        elif key == 'eos':
            eosPrepare()
            v0, e0, B, BP, residuals = eosFit()
            results[key] = {'V0' : v0, 'E0' : e0, 'B0' : B, 'BP' : BP, 'res' : residuals}
    return results

def compress():
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    if os.path.isfile('CHGCAR'):
        print('Compressing CHGCAR in ' + os.getcwd() + '.')
        execute('pigz -f -6 -p' + str(ncore) + ' CHGCAR')
       
    if os.path.isfile('WAVECAR'):
        print('Compressing WAVECAR in ' + os.getcwd() + '.')
        execute('pigz -f -6 -p' + str(ncore) + ' CHGCAR')
        
def decompress():
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    if os.path.isfile('CHGCAR.gz'):
        print('Decompressing CHGCAR.gz in ' + os.getcwd() + '.')
        execute('pigz -f -d -6 -p' + str(ncore) + ' CHGCAR.gz')
       
    if os.path.isfile('WAVECAR.gz'):
        print('Decompressing WAVECAR.gz in ' + os.getcwd() + '.')
        execute('pigz -f -d -6 -p' + str(ncore) + ' WAVECAR.gz')
        
def setupKP(settings,minkp):
    crystal = ase.io.read('POSCAR')
    cell = crystal.get_cell();
    a = cell[0];
    b = cell[1];
    c = cell[2];
    na = round(norm(a),3);
    nb = round(norm(b),3);
    nc = round(norm(c),3);
    nat = crystal.get_number_of_atoms()
    minkp /= nat

    lc = [na,nb,nc]
    kp = [int(x) for x in settings['KPOINTS']['K'].split()]
    small = float(min(lc))
    for i in range(0,3):
        ratio = round(kp[i]*small/lc[i],0)
        if ratio %2 == 0:
            ratio = ratio+1
            kp[i] = ratio

    print(kp)
    while(prod(kp) < minkp):
        kp[0] += 2
        kp[1] += 2
        kp[2] += 2
        for i in range(0,3):
            ratio = round(kp[i]*small/lc[i],0)
            if ratio %2 == 0:
                ratio = ratio+1
                kp[i] = ratio
    
    print(kp)
    settings['KPOINTS']['K'] = ' '.join([str(int(x)) for x in kp])
    return settings
    