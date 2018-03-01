from HighThroughput.communication.mysql import *
from HighThroughput.utils.generic import  *
import os,time,shutil

def abort():
    # either switch between electronic and ionic or auto based on ibrion
    print 'temp'
    return 0

def checkpointStart():
    print 'temp'
    return 0

def cont():
    #
    print 'temp'
    return 0

def finish():
    #end and readresults
    print ''
    return 0

def initialize():
    print 'write incar kpoints potcar, make directory?'
    return 0

def prepare(settings):
    parallelSetup(settings)
    print ''
    return 0

def getIBZPKT():
    curdir = os.getcwd()
    mkdir('temp')
    os.chdir(os.path.join(curdir,'temp'))
    shutil.copy2('../POSCAR','./POSCAR')
    shutil.copy2('../POTCAR','./POTCAR')
    shutil.copy2('../INCAR','./INCAR')
    shutil.copy2('../KPOINTS','./KPOINTS')
    genIBZKPT = subprocess.Popen('vasp',shell=True)
    while(not os.path.isfile(os.path.join(curdir,'temp','IBZKPT'))):
        time.sleep(1)
    genIBZKPT.kill()
    f = open('IBZKPT', 'r')
    lines = f.readlines()
    os.chdir(curdir)
    shutil.rmtree(os.path.join(curdir,'temp'))

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

def run(ratio,cwd = None):
    #could move hybrid to parallel setup
    if cwd == None:
        cwd = os.getcwd();
    cores = mysql_query('SELECT `cores` FROM `clusters` WHERE `name` = ' + str(os.getenv('VSC_INSTITUTE_CLUSTER')))
    hybrid = str(int(cores['cores'])/int(ratio))
    return execute('mympirun -h ' + hybrid + ' --output ' + cwd + '/tempout vasp')
    

def readSettings():
    print 't   '
    return 0

def parallelSetup():
    print ''
    return 0

def setupDir():
    print 'temp'
    return 0

def writeSettings():
    print ''
    return 0
