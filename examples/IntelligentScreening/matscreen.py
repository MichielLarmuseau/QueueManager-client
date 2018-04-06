# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os, random, re, shutil, subprocess, sys, time,math, json

import HighThroughput.manage.calculation as HT
import HighThroughput.manage.template as template
from HighThroughput.io.VASP import *
from HighThroughput.utils.generic import mkdir, execute
from HighThroughput.modules.VASP import *
from HighThroughput.errors.generic import *

qid = sys.argv[1]
submit_arg = '' + sys.argv[2] + ' ' + sys.argv[3] + ' ' + sys.argv[4]
submitscript = '' #this is what needs updating for auto error fix resubmit

# Set up the queue directory paths, this is always the same and should be moved to the .highthroughput file in a dictionary except for manual overrides
user = os.getenv('USER')
scratch = os.getenv('VSC_SCRATCH')


# Fetching a job and immediately starting it, ensuring we don't run the same job twice
print('Fetching...')
cinfo = HT.fetchgetstart(qid)
print('Fetched calculation ' + str(cinfo['id']))

if int(cinfo['id']) <= 0:
    print('No calculations left')
    sys.exit()
    
#Defining directories
qdir = os.path.join(os.getenv('VSC_SCRATCH'), 'queues', str(qid))
cdir = [os.path.join(qdir,'CALCULATIONS',cinfo['file'],x) for x in ['CALIB','RELAX/vol','RELAX/all','EOS/1.0','EOS/1.02','EOS/0.98','EOS/1.04','EOS/0.96','EOS/1.06','EOS/0.94','RELAX/internal','ENERGY','DOS','BANDS']]
cdir = [os.path.join(qdir,'import')] + cdir






# Starting the actual calculations

cinfo['settings'] = json.loads(cinfo['settings'])

status = int(cinfo['stat'])

print('Starting calculation ' + str(cinfo['id']) + ' on cluster: ' + cinfo['server'] + '.')

# Navigating to the directory of the current workflow step
os.chdir(os.path.join(qdir,'CALCULATIONS'))
mkdir(str(cinfo['file']))

os.chdir(os.path.join(qdir,'CALCULATIONS',cinfo['file']))
step = int(math.ceil(float(cinfo['stat'])/2))

# Configure settings per step
# By default always inherit
inheritcontcar = True
inheritchgcar = True
inheritwavecar = True
# Can define this by default, though I've added an if statement for each step anyways
inheritstep = step - 1
parent = HT.get(cinfo['parent'])
if parent['parent'] != 0:
    inheritmod = HT.getResults(parent['parent'])['settingsmod']
    
if step == 1:
    # Calibration
    inheritstep = 0
elif step == 2:
    # Vol relax
    inheritstep = 1
elif step == 3:
    # Full relax
    inheritstep = 2
elif step == 4:
    # EOS 1.0
    inheritstep = 3
elif step == 5:
    # EOS 1.02
    inheritstep = 4
elif step == 6:
    # EOS 0.98
    inheritstep = 4
elif step == 7:
    # EOS 1.04
    inheritstep = 5
elif step == 8:
    # EOS 0.96
    inheritstep = 6
elif step == 9:
    # EOS 1.06
    inheritstep = 7
elif step == 10:
    # EOS 0.94
    inheritstep = 8
elif step == 11:
    # Final internal relaxation
    inheritstep = 1
elif step == 12:
    # Final single point energy calculation
    inheritstep = 12
elif step == 13:
    # DOS
    inheritstep = 13
elif step == 14:
    # BANDS
    inheritstep = 14
#cleaning up certain chgcar and wavecars in later steps might be good
 
print('Starting step ' + str(step) + ' in ' + cdir[step] + '.')
mkdir(cdir[step])
os.chdir(cdir[step])

# Clearing
if os.path.isfile('aborted'):
    os.remove('aborted')

if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

# Start checkpointing, second argument should be how much time you need to write
# out the files necessary for restart, i. e. how much time before the walltime a 
# stop signal will be sent to your ab initio program.

# Could be automated based on LOOP time
checkpointStart(cinfo,1800)

# Here we continue the job if it was checkpointed in a previous job

if 'continue' not in parent['settings'].keys():
    parent['continue'] = 0
if 'continued' not in  parent['settings'].keys():
    parent['continued'] = 0

if int( parent['settings']['continue']) > int(parent['settings']['continued']):
    print('Continuing job from calculation id: ' + str(cinfo['parent']) + '.')
    cont(cinfo)
else:
    print('Initializing job.')
    print(cdir[inheritstep])
    inherit(cinfo,cdir[inheritstep],contcar=inheritcontcar,chgcar=inheritchgcar,wavecar=inheritwavecar,settingsmod=inheritmod)
    #Verify your potcardir, potgen should possibly just become a python function.
    initialize(cinfo['settings'])

if detectSP('POSCAR'):
    # This could be abstracted further, though the magnetic elements chosen in 
    # detectSP are not uniquely chosen either.
    cinfo['settings']['INCAR']['ISPIN'] = 2
        
#==============================================================================
# In this section you can also make manual changes to the settings, for example:
# if int(qid) == 167 or int(qid) == 171:
#     cinfo['settings']['KPOINTS']['K'] = '12 12 12'
#     cinfo['settings']['INCAR']['NKRED'] = '2'
# cinfo['settings']['INCAR']['LSUBROT'] = '.TRUE.'
# if int(cfile) == 10025486:
#     cinfo['settings']['INCAR']['ALGO'] = 'A'
#     cinfo['settings']['INCAR']['NELM'] = 30
#     cinfo['settings']['INCAR']['TIME'] = 1.95
# if int(cfile) == 10031153:
#     cinfo['settings']['INCAR']['MAGMOM'] = '2*1.0000 2*-1.0000'
#==============================================================================

parallelSetup(cinfo['settings'])


perror = parent['results']
if perror.get('errors') != None:
    fixerrors(cinfo)
writeSettings(cinfo['settings'])

#Preprocessing
# can check eos errors based on e-v.dat
decompress()
run()
compress()

# Error catching

finderrors(cinfo)

# Checkpoint cleanup
if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

print('Ending Calculation')

# Checkpoint abortion
if os.path.isfile('aborted'):
    print('Calculation aborted')
    execute(submitscript + ' ' + str(qid) + ' ' + str(submit_arg))
    sys.exit()
    
# Post-processing (run hooks? or extra functions in VASP module)

# Gather results and settings and end calculation

# Nowadays I take the energy with sigma -> 0, while in theory without entropy should be nearly the same, 
# this seems more robust and is also used by the VASP group

# Store detected errors
if 'error' in locals():
    HT.updateResults({'error':error}, cinfo['id'])
else:
    print('Gathering results')
    results = json.loads(cinfo['results'])
    results = gather(results)

    print('Updating results.')
# updateresults could be assumed from dictionary keys and automated.
    HT.updateResults(results, cinfo['id'])
    
        
    print('Energy OK. Ending calculation, deleting junk files and fetching results.')
    HT.end(cinfo['id'])
        #cleanup function
    # Can change this to a step dictionary
    os.remove('CHG')
    
print('Updating settings.')

# Update POTCAR INFO

POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
cinfo['settings']['POTCAR'] = POTCAR_version.strip().replace('\n',', ')

HT.updateSettings(cinfo['settings'], cinfo['id'])
newcalc = int(HT.fetch(str(qid)))

""" if newcalc > 0:
    execute(submitscript + ' ' + str(qid) + ' ' + str(submit_arg))
    print('Submitted new calculation in queue ' + str(qid) + '.')
else:
    print('Queue ' + str(qid) + ' is finished.')
"""
print('Calculation ended.')
