import json
import os
import socket
import csv
import datetime
from flask import Flask, send_file
#import pandas as pd

_KEBA_WALLBOX_IP = "***REMOVED***"
_KEBA_WALLBOX_PORT = 7090
_KEBA_WALLBOX_ADDR = (_KEBA_WALLBOX_IP,_KEBA_WALLBOX_PORT)
_KEBA_JSON_FILE = "c-keba.json"
_KEBA_CSV_FILE = "c-keba-export.csv"
_KEBA_CISCO_CSV_FILE = "***REMOVED***-keba-export.csv"
_Price = 0.49

app = Flask(__name__)

car_rfids = {
    '0000000000000000' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***'

}

def data_load():
    with open(_KEBA_JSON_FILE, 'r') as fp:
        return json.load(fp)

def data_save(data):
    os.rename(_KEBA_JSON_FILE,_KEBA_JSON_FILE+".bak")
    with open(_KEBA_JSON_FILE, 'w') as fp:
        json.dump(data, fp, indent=4)

def data_save_csv(history_json):
    data_file = open(_KEBA_CSV_FILE, 'w')
    data_file_***REMOVED*** = open(_KEBA_CISCO_CSV_FILE, 'w')
    data = history_json['history']
    data_***REMOVED*** = data = history_json['history'].copy()
    count=1
    csv_writer = csv.writer(data_file, dialect='excel', delimiter=';')
    csv_writer_***REMOVED*** = csv.writer(data_file_***REMOVED***, dialect='excel', delimiter=';')
    
    
    for r in sorted(data.keys()):
        if count == 1:
            header = data[str(r)].keys()
            csv_writer.writerow(header)
        csv_writer.writerow(data[str(r)].values())
        count += 1
    count = 1
    for r in sorted(data.keys()):
        if 'Curr HW' in data_***REMOVED***[str(r)]:
            data_***REMOVED***[str(r)].pop('Curr HW')
            data_***REMOVED***[str(r)].pop('started[s]')
            data_***REMOVED***[str(r)].pop('ended[s]')
            data_***REMOVED***[str(r)].pop('reason')
            data_***REMOVED***[str(r)].pop('timeQ')
            data_***REMOVED***[str(r)].pop('RFID tag')
            data_***REMOVED***[str(r)].pop('RFID class')
            data_***REMOVED***[str(r)].pop('Sec')
        if count == 1:
            header_***REMOVED*** = data_***REMOVED***[str(r)].keys()
            csv_writer_***REMOVED***.writerow(header_***REMOVED***)
        if int(data_***REMOVED***[str(r)]['E pres']) > 200 and data_***REMOVED***[str(r)]['Car'] is '***REMOVED***': 
            csv_writer_***REMOVED***.writerow(data_***REMOVED***[str(r)].values())
        count += 1



def init_socket():
    # Create a UDP socket and bind to ANY
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('0.0.0.0', _KEBA_WALLBOX_PORT) 
    s.bind(server_address)
    return s

def keba_recv(sock):
    while True:
        payload, address = sock.recvfrom(4096)
        if payload.startswith(b"{'E pres':"): continue
        if payload.startswith(b"{'Plug': "): continue
        if payload.startswith(b"{'Max curr': 0}"): continue
        if payload.startswith(b"{'Enable sys': 0}"): continue
        if payload.startswith(b"{'State': "): continue
        # suspress live updates as long we can't consume them
        break
    return (payload, address)

def keba_sendto(sock, msg):
    sock.sendto(msg.encode('utf-8'), _KEBA_WALLBOX_ADDR)
    data, address = keba_recv(sock)
    return data.decode('utf-8')   

def keba_getversion(sock):
    return keba_sendto(sock,"i")

def keba_getreport(sock,id):
    send_data = "report %d" % id
    return json.loads(keba_sendto(sock,send_data))

def keba_updatereports(sock, data):
    """updates data dict with latest reports"""
    for r in range(101, 131):
        report = keba_getreport(sock,r)
        
        try: 
            report['Car']=car_rfids[report['RFID tag']]
        except:
            report['Car']= 'unknown'

        
        energy = int(report['E pres']) / 10000
        report['Energy in kWh'] = str(round(energy,2)).replace('.',',')
        report['Price in Euro']= str(round(energy * _Price, 2)).replace('.',',')
        try:
            report['Year'] = datetime.datetime.strptime(report['started'], '%Y-%m-%d %H:%M:%S.%f').year
        except:
            report['Year'] = 0 
        try: 
            report['Month'] = datetime.datetime.strptime(report['started'], '%Y-%m-%d %H:%M:%S.%f').month
        except:
            report['Month'] = 0 
        print(report)
        report.pop('ID')
        cur_sessionid = report['Session ID']
        if cur_sessionid == -1: 
            continue
        data['history']["%d" % cur_sessionid]=report

@app.route('/')
# ‘/’ URL is bound with Keba Version
def startpage():
    keba_ver = keba_getversion(sock)
    output = "<p>Keba Report Downloader</p>"
    output = output + f"Keba Wallbox version: {keba_ver}"
    output = output + '<br><a href="http://127.0.0.1:5000/download">Download Full</a>'
    output = output + '<br><a href="http://127.0.0.1:5000/download***REMOVED***">Download ***REMOVED***</a>'
    output = output + '<br><a href="http://127.0.0.1:5000/update">Update</a>'

    return output

# Sending the file to the user
@app.route('/download')
def download():
   return send_file(_KEBA_CSV_FILE, as_attachment=True)

@app.route('/download***REMOVED***')
def download***REMOVED***():
   return send_file(_KEBA_CISCO_CSV_FILE, as_attachment=True)

@app.route('/update')
def web_update():
    keba_updatereports(sock, data)
    data_save(data)
    output = "Reports: %d" % (len(data['history']))
    output = output + '<br><a href="http://127.0.0.1:5000/">Back</a>'
    return output

if __name__ == "__main__":
    global sock, data
    sock = init_socket()
    keba_ver = keba_getversion(sock)
    print("Keba Wallbox version: %s" % keba_ver)
    data = data_load()
    keba_updatereports(sock, data)
    data_save(data)
    print(len(data['history']))
    data_save_csv(data)
    app.run()