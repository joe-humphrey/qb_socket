import socket
import threading
import socketserver
import win32com.client,xmltodict,datetime,json,time
import pythoncom
import sys,time,pywintypes,wmi,warnings,win32timezone
import pymysql as MySQLdb
import servicemanager
#print(sys.version)

try:
    sys_meipass = GetLongPathName(sys._MEIPASS)
except:
    sys_meipass = Path(__file__).resolve(strict=True).parent

dd = sys_meipass
gz = '''C:\\ProgramData\\config.txt'''
try:
    dic_list = open(gz, 'r')
    creds = eval(dic_list.read())
except Exception as e:
    servicemanager.LogErrorMsg('creds missing, needs config.txt in directory with %s.' % e )

gg = creds['l']+'\\PsExec.exe'
gs = creds['l']+'\\socketser.exe'

# '''where  the config.txt file contains a single dictionary of u, h , l, as u user of the system running QB, h passwd, and l as the housing directory of the QBListener , this executable, socketser.exe'''


def dbcalleroed(sql):                                                                      
    '''method to query db'''                                                                   
    try:                        
        __d2 = MySQLdb.connect(host=creds['dbh'],port=3306,user=cred['dbu'],passwd=creds['dbp'],db='SocketComputers', charset = 'utf8', use_unicode = True,cursorclass = MySQLdb.cursors.DictCursor)
        cursor3 = __d2.cursor()
        warnings.filterwarnings("ignore", category=MySQLdb.Warning)
        cursor3.execute(sql)
        results = cursor3.fetchall()         
        cursor3.close()
        __d2.commit() 
        __d2.close()
    except Exception as e:
        res = 'no db lookup with %s' % e
        results = None
    return results

sqlz = '''select EntryID,UsedPort as UserPort FROM SocketComputers.PortMap WHERE Application = 'QBSocketSrv' '''
sqlr = '''select EntryID from SocketComputers.Computer WHERE IPAddress = '%(IP)s',PortMapID = '%(EntryID)s' '''
sqli = '''INSERT INTO SocketComputers.Computer(IPAddress,PortMapID,HeartbeatTimeStamp)values('%(IP)s','%(EntryID)s',NOW()) '''
sqlu = '''UPDATE SocketComputers.Computer SET HeartbeatTimeStamp = NOW() WHERE PortMapID = '%(EntryID)s' AND IPAddress = '%(IP)s' '''
sqlq = '''DELETE FROM SocketComputers.Computer WHERE PortMapID = '%(EntryID)s' AND IPAddress = '%(IP)s' '''

sys.coinit_flags = 0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('192.168.0.1', 1))  # connect() for UDP doesn't send packets
local_ip_address = s.getsockname()[0]


def IsRunning(WindowName):
    servicemanager.LogInfoMsg('IsRunning, thread id %s' % threading.get_ident())
    f = wmi.WMI()
    flag = False
    # Iterating through all the running processes
    try:
        for process in f.Win32_Process():
            if WindowName == process.Name:
                flag = True
                return flag
    except:
        print("Application is not Running")
    return flag

def func1(data,**kwargs):
    cmds = []
    if 'tcnt' in kwargs:
        tcnt = kwargs['tcnt']
        tcnt += 1
    else:
        tcnt = 0
    for idx,key in enumerate(data.keys()):
        if isinstance(data[key],str):
            if 'datetime' in data[key]:
                if 'okey' in kwargs:
                    cmds.append(str(kwargs['okey']) + '''.''' + str(key) + '''(''' + str(data[key]) + ''')''')
                else:
                    cmds.append(str(key) + '''(''' + data[key] + ''')''')
            else:
                if 'okey' in kwargs:
                    cmds.append(str(kwargs['okey']) + '''.''' + str(key) + '''(''' + '''\'''' + str(data[key]).strip("'") + '''\'''' + ''')''')
                else:
                    cmds.append(str(key) + '''(''' + '''\'''' + str(data[key]).strip("'") + '''\'''' + ''')''')
        if isinstance(data[key], bool):
            if 'okey' in kwargs:
                cmds.append(str(kwargs['okey']) + '''.''' + str(key) + '''(''' + '''\'''' + str(data[key]) + '''\'''' + ''')''')
            else:
                cmds.append(str(key) + '''(''' + str(data[key]) + ''')''')
        if isinstance(data[key], (list)):
            if all([isinstance(v,str) for v in data[key]]):
                if 'okey' in kwargs:
                    cmds.append(str(kwargs['okey']) + '''.''' + str(key) + '''(''' + '''\'''' + str(data[key]).strip("'") + '''\'''' + ''')''')
                else:
                    cmds.append(str(key) + '''(''' + '''\'''' + str(data[key]).strip("'") + '''\'''' + ''')''')
            else:
                for xx,i in enumerate(data[key]):
                    if isinstance(i,str):
                        if 'okey' in kwargs:
                            cmds.append(str(kwargs['okey']) + '''.''' + str(key) + '''(''' + '''\'''' + str(i).strip("'") + '''\'''' + ''')''')
                        else:
                            cmds.append(str(key) + '''(''' + '''\'''' + str(i).strip("'") + '''\'''' + ''')''')
                    elif isinstance(i, (list)):
                        if 'okey' in kwargs:
                            cz = func1(i,okey=(str(kwargs['okey']) + '.' + key),tcnt=tcnt)
                        else:
                            nkey = '''othz''' + str(xx)
                            cmds.append(str(nkey) + ''' = th.''' + key )
                            cz = func1(i,okey=nkey)
                    else:
                        if 'okey' in kwargs:
                            if tcnt == 0:
                                cz = func1(i,okey=str(kwargs['okey'] + '.' + key),tcnt=tcnt)
                            else:
                                nkey = '''thz''' + str(tcnt)
                                cmds.append(str(nkey) + ''' = ''' + kwargs['okey'] + '''.''' + key )
                                cz = func1(i,okey=nkey,tcnt=tcnt)
                        else:
                            nkey = '''thz''' + str(tcnt)
                            cmds.append(str(nkey) + ''' = th.''' + key )
                            cz = func1(i,okey=nkey,tcnt=tcnt)
                        cmds.extend(cz)
        elif isinstance(data[key], dict):
            if 'okey' in kwargs:
                cz = func1(data[key],okey=(str(kwargs['okey']) + '.' + key),tcnt=tcnt)
            else:
                cz = func1(data[key],okey=key,tcnt=tcnt)
            cmds.extend(cz)
    return cmds

def retparser(zz):
    #zz = responseMsgSet.ToXMLString()
    cc = xmltodict.parse(zz)
    try:
        ccc = cc['QBXML']["QBXMLMsgsRs"]
        flv = ccc.keys()[0]
        retl = [ k for k in ccc[flv].keys() if 'Ret' in k][0]
        ccct = ccc[flv][retl]
        outj = json.dumps(ccct)
    except:
        outj = 'failed response'
    return outj

def dictparser(zz):
    cc = xmltodict.parse(zz)
    try:
        ccc = cc['QBXML']["QBXMLMsgsRs"]
        #print(ccc.keys())
        flv = list(ccc.keys())[0]
        retl = [ k for k in list(ccc[flv].keys()) if 'Ret' in k][0]
        ccct = ccc[flv][retl]
        #outj = json.dumps(ccct)
    except Exception as e:
        ccct = 'failed response %s with %s' % (e,cc)
    return ccct

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def handlerzbak(inpdata):
    ret = 'is blank'
    try:
        if is_json(inpdata):
            cdict = json.loads(inpdata)
            pcall = cdict['action']
            ret = func1(cdict['value'])
    except:
        ret = 'failed'
    return ret

def handlerz(inpdata):
    ret = 'is blank'
    try:
        if is_json(inpdata):
            cdict = json.loads(inpdata)
            pcall = cdict['action']
            calls = func1(cdict['value'])
            sessionManager = win32com.client.Dispatch("QBFC10.QBSessionManager")
            if threading.current_thread() is not threading.main_thread():
                servicemanager.LogInfoMsg('not main thread, thread id %s' % threading.get_ident())
            else:
                servicemanager.LogInfoMsg('is main thread, thread id %s' % threading.get_ident())
            #print('after session',threading.current_thread().name)   
            sessionManager.OpenConnection('', 'SDKTest')
            sessionManager.BeginSession('', 2)
            requestMsgSet = sessionManager.CreateMsgSetRequest("US", 10, 0)
            thw = 'th = requestMsgSet.' + pcall + '''()'''
            exec(thw)
            for iz in calls:
                print(iz[:3])
                if iz[:3] == 'thz':
                    cmd = iz
                else:
                    cmd = 'th.' + iz
                print(cmd)
                exec(cmd)
            responseMsgSet = sessionManager.DoRequests(requestMsgSet)
            zz = responseMsgSet.ToXMLString()
            sessionManager.EndSession()
            sessionManager.CloseConnection()
            ret = dictparser(zz)
        else:
            ret = 'Object not json'
    except Exception as e:
        ret = 'failed with %s' % e
    return ret


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        lengthbuf = self.request.recv(10)
        length = int(lengthbuf)
        timeout = time.time() + 30
        timed = ''
        datab = b''
        while length:
            if time.time() > timeout:
                timed = 'set'
                break
            newbuf = self.request.recv(length)
            if not newbuf: return None
            datab += newbuf
            length -= len(newbuf)
        if not timed:
            data = str(datab, 'ascii')
            rets = handlerz(data)
            ret = json.dumps(rets,indent=4)
            dest = bytes(str(len(ret)).rjust(10,'0'),'ascii')
            self.request.sendall(dest)
            response = bytes(ret,'ascii')
        else:
            rets = '''timeout reached'''
            ret = json.dumps(rets,indent=4)
            dest = bytes(str(len(ret)).rjust(10,'0'),'ascii')
            self.request.sendall(dest)
            response = bytes(ret,'ascii')
        try:
            self.request.sendall(response)
            if local_ip_address and mport:
                sqluu = sqlu % {'IP':local_ip_address,'EntryID':mport[0]['EntryID']}
                dbcalleroed(sqluu)
        except Exception as e:
            print(e)
        #pythoncom.CoUninitialize()


def finalcountdown(IP,EntryID):
    while True:
        time.sleep(300)
        if IsRunning('QBW32.EXE'):
            sqlcc = sqlu % {'IP':IP,'EntryID':EntryID}
            dbcalleroed(sqlcc)
        else:
            print('QB not running, exiting.')
            sqlqq = sqlq % {'IP':IP,'EntryID':EntryID}
            dbcalleroed(sqlqq)
            os._exit(1)

mport = dbcalleroed(sqlz)

if __name__ == "__main__":
    if mport is not None and mport[0].get('UserPort',None) is not None:
        pport = int(mport[0]['UserPort'])
    else:
        pport = None
    HOST = local_ip_address if local_ip_address else None
    with socketserver.TCPServer((HOST, pport), ThreadedTCPRequestHandler) as server:
        #if IsRunning('QBW32.EXE'):
        if mport is not None:
            sqlic = dbcalleroed(sqlr % {'IP':HOST,'EntryID':mport[0]['EntryID']})
            if not sqlic:
                sqlii = sqli % {'IP':HOST,'EntryID':mport[0]['EntryID']}
                dbcalleroed(sqlii)
            else:
                sqluu = sqlu % {'IP':HOST,'EntryID':mport[0]['EntryID']}
                dbcalleroed(sqluu)
        server.serve_forever()
        #else:
        #    servicemanager.LogInfoMsg('QuickBooks does not seem to be running, exiting.')
        #    sys.exit(1)
