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
submitscript = ''

# Set up the queue directory paths, this is always the same and should be moved to the .highthroughput file in a dictionary except for manual overrides
user = os.getenv('USER')

if os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
    qdir = os.path.join('/scratch/leuven/' + user.replace('vsc','')[0:3] + '/' + user, 'queues', str(qid))
else:
    qdir = os.path.join('/user/scratch/gent/' + user[0:-3] + '/vsc40479', 'queues', str(qid))

# Fetching a job and immediately starting it, ensuring we don't run the same job twice
print('Fetching...')
cinfo = HT.fetchgetstart(qid)
print('Fetched calculation ' + str(cinfo['id']))

if int(cinfo['id']) <= 0:
    print('No calculations left')
    sys.exit()
    
# Starting the actual calculations

cinfo['settings'] = json.loads(cinfo['settings'])

status = int(cinfo['stat'])

print('Starting calculation ' + str(cinfo['id']) + ' on cluster: ' + cinfo['server'] + '.')

# Navigating to the directory of the current workflow step
os.chdir(os.path.join(qdir,'CALCULATIONS'))
mkdir(str(cinfo['file']))

os.chdir(os.path.join(qdir,'CALCULATIONS',cinfo['file']))
step = int(math.ceil(float(cinfo['stat'])/2))
print('Starting step ' + str(step))
mkdir('./STEP' + str(step))
os.chdir('./STEP' + str(step))

# Clearing
if os.path.isfile('aborted'):
    os.remove('aborted')

if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

# Start checkpointing, second argument should be how much time you need to write
# out the files necessary for restart, i. e. how much time before the walltime a 
# stop signal will be sent to your ab initio program.

# Could be automated based on LOOP time
checkpointStart(cinfo,3600)

# Here we continue the job if it was checkpointed in a previous job
parent = HT.getSettings(cinfo['parent'])

if 'continue' not in parent.keys():
    parent['continue'] = 0
if 'continued' not in parent.keys():
    parent['continued'] = 0

if int(parent['continue']) > int(parent['continued']):
    print('Continuing job from calculation id: ' + str(cinfo['parent']) + '.')
    cont(cinfo)
else:
    print('Initializing job.')
    inherit(status,qdir,cfile)
    initialize(cinfo['settings'])

if detectSP('POSCAR'):
    # This could be abstracted further, though the magnetic elements chosen in 
    # detectSP are not uniquely chosen either.
    cinfo['settings']['INCAR']['ISPIN'] = 2
    
#Test settings
cinfo['settings']['INCAR']['ENCUT'] = 200
cinfo['settings']['KPOINTS']['K'] = '1 1 1'
    
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
#if os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
#    cinfo['settings']['INCAR']['NCORE'] = '28'
perror = HT.getResults(cinfo['parent'])
if perror.get('errors') != None:
    fixerrors(cinfo)
writeSettings(cinfo['settings'])

#Preprocessing
# can check eos errors based on e-v.dat

run()

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
    print('Energy OK. Ending calculation, deleting junk files and fetching results.')
    HT.end(cinfo['id'])
        #cleanup function
    # Can change this to a step dictionary
    os.remove('CHG')
    
    print('Gathering results')
    results = json.loads(cinfo['results'])
    results = gather(results)

    print('Updating results.')
# updateresults could be assumed from dictionary keys and automated.
    HT.updateResults(results, cinfo['id'])

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
