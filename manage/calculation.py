from ..communication.mysql import mysql_query
import json,os,re
import HighThroughput.io.CIF as CIF

calcid = 0;
sw = '';
stat = 0;
def fetchgetstart(qid):
    global calcid, sw, stat
    calc = mysql_query('FETCHGETSTART ' + str(qid) + ' ' + os.getenv('VSC_INSTITUTE_CLUSTER') + ' ' + str(os.getenv('PBS_JOBID')).split('.')[0] )
    calcid = calc['id']
    sw = calc['software']
    stat = calc['stat']
    return calc

def fetch(qid):
    return mysql_query('FETCHQ ' + str(qid))

def add(material,queue,priority = '',settings = None,results = None, status = 0):
    global calcid, stat, sw
    #API conflict
    wftemplate = mysql_query('SELECT `priority`, `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' + str(queue) + ') AND `stat` = ' + str(status))
    print(wftemplate)
    if settings == None:
        settings = wftemplate['stemplate']

    if results == None:
        results = wftemplate['rtemplate']

    software = ''

    if isinstance(settings, dict):
        settings = json.dumps(settings)
        print('Be sure to update the software type.')
    elif str(settings).isdigit():
        print(settings)
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(settings))
        settings = template['template']
        software = template['software']

    if isinstance(results, dict):
        results = json.dumps(results)
        print('Be sure to update the software type.')
    elif str(results).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(results))
        results = template['template']
        software = template['software']

    sw = software

    if priority == '':
        priority = wftemplate['priority']

    owner = mysql_query('');
    result = mysql_query('INSERT INTO `calculations` (`queue`, `priority`, `owner`, `results`, `settings`, `software`, `file`, `stat`,`leaf`) VALUES (' + str(queue) + ', ' + str(priority) + ', ' + str(owner) + ',  \'' + results + '\', \'' + settings + '\', \'' + software + '\', ' + str(material) + ', ' + str(status) + ',1)');
    cid = result
    calcid = result
    queue = mysql_query('SELECT `id`, `name` FROM `queues` WHERE `id` = ' + str(queue))

    if(int(result) > 0):
        print('Added calculation for material ' + str(material) + ' (' + str(cid) + ') to the ' + queue['name'] + ' queue (' + str(queue['id']) + ') as calculation ' + str(cid)  + '.')
    else:
        print('Adding calculation for material ' + str(material) + ' to the ' + queue['name']  + ' queue (' + str(queue['id']) + ') failed.')
    return cid

def modify(params):
    query = 'UPDATE `calculations` SET '
    for key in params.keys():
        if key != 'id':
            query += '`' + key  + '` ='
            if isinstance(params[key],dict):
                query  += '\'' + json.dumps(params[key]) + '\''
            elif not str(params[key]).isdigit():
                query += '\'' + str(params[key]) + '\''
            else:
                query += str(params[key])
            query += ', '
    query = query[:-2] + ' WHERE `id` = ' + str(params['id'])
    query = query.translate(str.maketrans({"'":  r"\'"}))
    result = int(bool(mysql_query(query)))
    print('Modify query' + query)
    if (result == 1):
        print('The calculation has been modified. Please verify.')
    elif (result == 0):
        print('Nothing to modify.')
    else:
        print('Help... Me...')
    return result

def getSettings(cid = None):
    if(cid == None):
        cid = calcid
    result = mysql_query('SELECT `settings` FROM `calculations` WHERE `id` = ' + str(cid))
    return json.loads(result['settings'])

def getResults(cid = None):
    if(cid == None):
        cid = calcid
    result = mysql_query('SELECT `results` FROM `calculations` WHERE `id` = ' + str(cid))
    return json.loads(result['results'])


def updateSettings(settings,cid = None):
    if(cid == None):
        cid = calcid

    if isinstance(settings, dict):
        settings = json.dumps(settings)
    elif str(settings).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(settings))
        settings = template['template']

    tempdict = {'id' : cid, 'settings': settings}
    return modify(tempdict)

def updateResults(results,cid = None):
    if(cid == None):
        cid = calcid

    if isinstance(results, dict):
        results = json.dumps(results)
    elif str(results).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(results))
        results = template['template']

    print('Updating results of calculation ' + str(cid) + ' to ' + results + '.')
    tempdict = {'id' : cid, 'results': results}
    return modify(tempdict)

def remove(cid):
    result = mysql_query('DELETE FROM `calculations` WHERE `id` = ' + str(cid))
    if (result == '1'):
        print('Calculation ' + str(cid) + ' has been removed.')
    else:
        print('Removing calculation ' + str(cid) + ' has failed.')

def get(cid):
    global calcid, sw, stat;

    material = mysql_query('SELECT `file` FROM `calculations` WHERE `id` = ' + str(cid))


    if isinstance(material, str):
        return material
    
    if(int(material['file']) < 10000000):
        table = 'data'
    else:
        table = 'newdata'

    result = mysql_query('SELECT * FROM `calculations` JOIN `' + table + '` ON (`calculations`.`file` = `' + table + '`.`file`) WHERE `calculations`.`id` = ' + str(cid))
    result['results'] = json.loads(result['results'])
    result['settings'] = json.loads(result['settings'])

    if not isinstance(result, str):
        calcid = cid
        sw = result['software']
        stat = result['stat']
    else:
        print('Retrieving calculation ' + str(cid) + ' failed.')
    return result

def start(cid = None):
    global stat,sw
    status = 0
    manual = True
    if cid == None:
        cid = calcid
        manual = False

    if(int(cid) > 0):
        calc = mysql_query('SELECT * FROM `calculations` WHERE `id` = ' + str(cid))
        if manual == False:
            status = stat
        else:
            status = calc['stat']
        #already = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `queue` = ' + calc['queue'] + ' AND `file` = ' + calc['file'] + ' AND `stat` IN (' + str(int(calc['stat'])+1) + ', ' + str(int(calc['stat'])+2) + ' AND `start` > DATE_SUB(NOW(), INTERVAL 1 HOUR))')
        already = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `parent` = ' + str(calc['id']))

        if int(status) % 2 != 0 or int(already['count']) > 0:
            return 0

        #restart = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `queue` = ' + calc['queue'] + ' AND `file` = ' + calc['file'] + ' AND `stat` = ' + calc['stat'])
        # and restart['count'] == 1
        status = int(status) + 1
#using stat here as global feels a bit dodgy
        wftemplate = mysql_query('SELECT `priority`, `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' + str(calc['queue']) + ') AND `stat` = ' + str(status))
        if(int(wftemplate['rtemplate']) > 0):
            results =wftemplate['rtemplate']
        else:
            results = calc['results']

        if(int(wftemplate['stemplate']) > 0):
            settings = wftemplate['stemplate']
        else:
            settings = calc['settings']

        if isinstance(wftemplate,str):
            priority = calc['priority']
        else:
            priority = wftemplate['priority']
        print(priority)
        sw=calc['software']
        add(calc['file'],calc['queue'],priority, settings, results, status)
        mysql_query('UPDATE `calculations` SET `parent` = ' + str(cid) + ' WHERE `id` = ' + str(calcid))
        cid = calcid
        stat = status
        return int(mysql_query('UPDATE `calculations` SET `start` = NOW(), `server` = \'' + str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + str(os.getenv('PBS_JOBID')) + '\' WHERE `id` = ' + str(cid)));

def restart(cid = None):
    global stat,calcid
    #problem with 0 case
    status = 0
    manual = True
    settings = ''
    results = ''
    if cid == None:
        cid = calcid
    calc = get(cid)
    stat = int(calc['stat'])
    if(int(cid) > 0):
        if stat % 2 != 0:
            stat = stat - 1
            rollback(stat)
            calc = get(cid)
            return 1
        else:
            stat = stat - 2
            rollback(stat)
            calc = get(cid)
            return 1

        cid = calcid

        status = stat

        wftemplate = mysql_query('SELECT `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' +     str(calc['queue']) + ') AND `stat` = ' + str(status))
        if(int(wftemplate['rtemplate']) > 0):
            template = mysql_query('SELECT `template` FROM `templates` WHERE `id` = ' + str(wftemplate['rtemplate']))
            results = template['template']
        else:
            results = calc['results']

        if(int(wftemplate['stemplate']) > 0):
            template = mysql_query('SELECT `template` FROM `templates` WHERE `id` = ' + str(wftemplate['stemplate']))
            settings = template['template']
        else:
            settings = calc['settings']

    return int(mysql_query('UPDATE `calculations` SET `stat` = ' + str(status) + ', `start` = 0, `end` = 0, `server` = \'' + str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + str(os.getenv('PBS_JOBID').split('.')[0]) + '\', `settings` = \'' + settings + '\', `results` = \'' + results + '\', `leaf` = 1 WHERE `id` = ' + str(cid)));

def rollback(status, cid=None):
    global calcid, stat
    manual = True
    if cid != None:
        calcid = cid
    current = get(calcid)
    while int(current['stat']) > int(status) and not isinstance(current,str):
        oldcid = current['id']
        current = get(current['parent'])
        if isinstance(current,str):
            restart(oldcid)
            break
        else:
            mysql_query('DELETE FROM `calculations` WHERE `id` = ' + str(oldcid))
            calcid = current['id']
    modify({'id' : current['id'], 'leaf': 1})
    return 1

def showAll(qid):
    return mysql_query('SELECT * FROM `calculations` WHERE `queue` = ' + str(qid))

def end(cid = None):
    global stat
    status = 0
    manual = True
    if cid == None:
        cid = calcid
        manual = False
    if(int(cid) > 0):
        if manual == False:
            stat = int(stat) + 1
            status = stat
        else:
            status = mysql_query('SELECT `stat` FROM `calculations` WHERE `id` = ' + str(cid))
            status = int(status['stat'])+1
        output = {'VASP' : 'CONTCAR', 'Gaussian' : str(cid) + '.log'}
        CIFtext = ''
        if sw:
            if sw in output.keys():
                if os.path.isfile(output[sw]):
                    cif = CIF.read(output[sw],sw)
                    CIFtext = CIF.write('temp.cif',cif)
                    os.remove('temp.cif')

        return int(bool(mysql_query('UPDATE `calculations` SET `stat` = ' + str(status) + ', `end` = NOW(), `server` = \'' +str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + str(os.getenv('PBS_JOBID')).split('.')[0] + '\', `cif` = \'' + CIFtext.replace('\'','\\\'') + '\' WHERE `id` = ' + str(cid))));
    else:
        return 0

def setPriority(priority,cid = None):
    if cid == None:
        cid = calcid

    if(str(priority).isdigit()):
        return mysql_query('UPDATE `calculations` SET `priority` = ' + str(priority) + ' WHERE `id` = ' + str(cid))
    else:
        print('Priorities are number, the higher the number the higher the priority')
    return 0
