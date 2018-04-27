# -*- coding: utf-8 -*-
from HighThroughput.communication.mysql import mysql_query
import pandas as pd
import json

def getComposition(queue,stat):
    rows = mysql_query('SELECT `newdata`.`file`, `newdata`.`calcformula` FROM `calculations` INNER JOIN  WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
    
    compdict = {'file' : []}
    for row in rows:
        compdict['file'].append(row['file'])
        
        formula = row['formula'].split()
        stoich = [ [i for i in x if i.isdigit()] for x  in formula]
        els = [ [i for i in x if not i.isdigit()] for x  in formula]
        
        for i in range(len(els)):
            if 'el' + str(i) not in compdict:
                compdict['el' + str(i)] = []
                compdict['stoich' + str(i)] = []
            
            compdict['el' + str(i)].append(els[i])
            compdict['stoich' + str(i)].append(stoich[i])
                
    composition = pd.DataFrame(compdict, index = 'file')
    composition.fillna(0)
    return composition
    
def getFile(queue,stat):
     rows = mysql_query('SELECT `file` FROM `calculations` WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
        
     file = []
     
     for row in rows:
        file.append(row['file'])
        
     ID = pd.DataFrame({'file' : file})
     return ID

def getResults(queue,stat,keys):
    rows = mysql_query('SELECT `file`, `results` FROM `calculations` WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
    
    keys.insert(0,'file')
    
    resultsdict = { 'file' : []}
    
    for key in keys:
        resultsdict[key] = []
        
    for row in rows:
        resultsdb = json.loads(row['results'])
        for key in keys:
            resultsdict[key].append(resultsdb[key])
        
    results = pd.DataFrame(resultsdict, index = 'file')
    return results

