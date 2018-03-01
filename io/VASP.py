import os

def readINCAR(directory=os.getcwd()):
    if directory == None:
        directory = os.getcwd()
    template = dict()
    INCAR = open(os.path.join(directory,'INCAR'),'r') 

    for line in INCAR:
        settings = line.split('=')
        if len(settings) < 2:
            continue
        settings[1] = settings[1].split('!')
        template[settings[0].strip()] = settings[1][0].strip()

    INCAR.close()
    return template

def writeINCAR(template,directory=None):
    print template
    if directory == None:
        directory = os.getcwd()
    INCAR = open(os.path.join(directory,'INCAR'),'w')

    for key,value in sorted(template.iteritems()):
        INCAR.write(str(key) + ' = ' + str(value) + '\n')

    return INCAR.close()

def readKPOINTS(directory=None):
    if directory == None:
        directory = os.getcwd()
    template = dict()
    KPOINTS = open(os.path.join(directory,'KPOINTS'),'r') 
        
    kfile = filter(None,map(lambda s: s.strip(), KPOINTS.readlines()))
    
    if int(kfile[1]) != 0:
        template['file'] = '\n'.join(kfile)
    else:
        template['comment'] = kfile[0]
        template['mode'] = kfile[2][0].upper()
        if template['mode'] == 'A':
            template['L'] = int(kfile[3])
        else:
            #k = kfile[3].split()
            #template['kx'] = int(k[0])
            #template['ky'] = int(k[1])
            #template['kz'] = int(k[2])
            template['K'] = kfile[3]
            template['shift'] = kfile[4]
    return template

def writeKPOINTS(template,directory=None):
    if directory == None:
        directory = os.getcwd()
    KPOINTS = open(os.path.join(directory,'KPOINTS'),'w')
    modedict = {'A' : 'Auto', 'M' : 'Monkhorst Pack', 'G' : 'Gamma'}
    if not template['mode']:
        kfile = str(template['file'])
    else:
        kfile = str(template['comment']) + '\n0\n' + modedict[str(template['mode'])] + '\n'

        if template['mode'] == 'A':
            kfile += str(template['L'])
        else:
            kfile += str(template['K']) + '\n' + str(template['shift'])

    KPOINTS.write(kfile)
    return KPOINTS.close()
    
        
