import socket
import threading
import socketserver
import win32com.client,xmltodict,datetime,json,time,os,asyncio,subprocess
from win32api import GetLongPathName
import pythoncom
import sys,time,pywintypes,wmi,warnings,win32timezone
import pymysql as MySQLdb
import win32serviceutil  # ServiceFramework and commandline helper
import win32service  # Events
import win32event
import servicemanager  # Simple setup and logging
from pathlib import Path



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
s.close()

def IsRunning(WindowName):
    servicemanager.LogInfoMsg('IsRunning, thread id %s' % threading.get_ident())
    f = wmi.WMI()
    flag = False
    # Iterating through all the running processes
    try:
        for process in f.Win32_Process():
            if WindowName == process.Name:
                flag = True
                break
    except:
        ("Application is not Running")
    return flag

def qbsessfnder():
    f = wmi.WMI()
    flag = 1
    # Iterating through all the running processes
    try:
        flag = f.win32_process(name='QBW32.exe')[0].SessionId
    except:
        ("Application is not Running")
    return flag


def finalcountdown(IP,EntryID):
    while True:
        time.sleep(300)
        if IsRunning('QBW32.EXE'):
            sqlcc = sqlu % {'IP':IP,'EntryID':EntryID}
            dbcalleroed(sqlcc)
        else:
            sqlqq = sqlq % {'IP':IP,'EntryID':EntryID}
            dbcalleroed(sqlqq)

class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "QBListener"
    _svc_display_name_ = "QBListener Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)
        #self.server = socketserver
        self.isrunning = False
        self.loop = asyncio.new_event_loop()
        self.mport = dbcalleroed(sqlz)
        # Port 0 means to select an arbitrary unused port
        if self.mport is not None and self.mport[0].get('UserPort',None) is not None:
            self.pport = int(self.mport[0]['UserPort'])
        else:
            self.pport = 11111
        self.HOST = local_ip_address if local_ip_address else None

    def SvcStop(self):
        sqlqq = sqlq % {'IP':self.HOST,'EntryID':self.mport[0]['EntryID']}
        dbcalleroed(sqlqq)
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        #self.process.terminate()
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        #self.server.shutdown()


    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        try:
            
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            servicemanager.LogInfoMsg("Starting service")
            pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
            self.start()
            if self.isrunning:
                self.main()
            #while self.runflag == True:
            #    pass
            win32event.WaitForSingleObject(self.stop, win32event.INFINITE)
        except Exception as e:
            servicemanager.LogErrorMsg(str(e))
            pythoncom.CoUninitialize()

    def start(self):
        #pythoncom.CoInitialize()
        self.isrunning = True #IsRunning('QBW32.EXE')  # made change here to auto start without QB running
        #if not os.startfile("C:\\Users\\mac\\dist\\socketser.exe"):
        #    self.isrunning = False
        #pythoncom.CoUninitialize()
        #self.main()

    def stop(self):
        os.system("taskkill /f /im socketser.exe")
        self.isrunning = False
        servicemanager.LogInfoMsg('loop close attempt')
        try:
            self.loop.close()
        except Exception as e:
            servicemanager.LogErrorMsg('close loop attempt failed with %s' % e) 


    def main(self):
        ccmd = [gg,"-accepteula","-i",str(qbsessfnder()),"-u",creds['u'],"-p",creds['h'],gs]
        #ccmd = [gg,"-accepteula","-i","1",gs]
        servicemanager.LogInfoMsg('running cmd %s' % ccmd )
        if not subprocess.call(ccmd):
        #if not subprocess.call(["C:\\Users\mac\dist\socketser.exe"]):
            self.isrunning = False
            servicemanager.LogErrorMsg('startfile failed')
        else:
            servicemanager.LogInfoMsg('started socketser')
        while self.isrunning:
            try:
                asyncio.set_event_loop(self.loop)
                servicemanager.LogInfoMsg('loop attempt')
                self.loop.run_forever()
            finally:
                servicemanager.LogInfoMsg('loop failed to run')
                self.loop.close()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AppServerSvc)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AppServerSvc)

