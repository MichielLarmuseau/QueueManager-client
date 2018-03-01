#!/usr/bin/env python
from HighThroughput.communication.mysql import *
import re


files = mysql_query('select newdata.file,newdata.text,newdata.formula,newdata.calcformula,queue from calculations inner join newdata on calculations.file = newdata.file where calculations.queue = 237 and calculations.stat = 0')


for file in files:
    text = re.findall('[A-Z][^A-Z]*', file['text'])
    #text.insert(1,'6')
    #text.insert(4,'4')
    #text.append('3')
    print 'UPDATE zintlfinal set text = \'' + ''.join(text) + '\' where file = ' + file['file'] + ';'

