import httplib,urllib,json,os.path
from datetime import datetime

def mysql_query(query,blob=''):
    configfile= open(os.path.expanduser('~') + '/.highthroughput','r')
    login = json.loads(configfile.read())
    conn = httplib.HTTPConnection('physics.epotentia.com',timeout=900)
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    params = urllib.urlencode({'query' : query, 'blob' : blob, 'email' : login['email'], 'token' : login['token']})
    conn.request('POST','/apis/api.beta0.0.2.php',params,headers)
    response = conn.getresponse().read()
    try: 
        data = json.loads(response)
        if len(data) == 1:
            data = data[0]
    except:
	    data = response
    conn.close()
    return data

def mysql_query_profile(query,blob=''):
    startTime = datetime.now()
    print('\n\nstart')
    configfile= open(os.path.expanduser('~') + '/.highthroughput','r')
    login = json.loads(configfile.read())
    print('load config')
    print(datetime.now() - startTime)
    conn = httplib.HTTPConnection('www.darkawake.com')
    print('connected')
    print(datetime.now() - startTime)
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    params = urllib.urlencode({'query' : query, 'blob' : blob, 'email' : login['email'], 'token' : login['token']})
    print('encoded')
    print(datetime.now() - startTime)
    conn.request('POST','/compmat/api2.php',params,headers)
    print('posted')
    print(datetime.now() - startTime)
    response = conn.getresponse().read()
    print('read response')
    print(datetime.now() - startTime)
    try: 
        data = json.loads(response)
        if len(data) == 1:
            data = data[0]
    except:
        data = response
    print('json parsed')
    print(datetime.now() - startTime)
    print('\n\n')
    return data

owner = mysql_query('')
