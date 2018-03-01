import json, os, subprocess, sys

def execute(command):
    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    print out
    print >> sys.stderr, err

    if err in locals():
        #raise Exception('Error in executing bash-command.')
        return False
    else:
        return out

def mkdir(command):
    if not os.path.isdir(command):
        os.mkdir(command)

def remove(command):
    if os.path.isfile(command):
        os.remove(command)
    else:
        print(str(command)+' is not a file.')

def error_catch(command):
    try:
        execute(command)
        return True
    except:
        return False

def getNodeInfo():
    from collections import Counter
    nodefile = subprocess.Popen('cat $PBS_NODEFILE',stdout=subprocess.PIPE,shell=True)
    nodefile = [x.split('.')[0].replace('node','') for x in filter(None,nodefile.communicate()[0].split('\n'))]
    corecount = Counter()
    for node in nodefile:
        corecount[node] += 1
    return corecount

