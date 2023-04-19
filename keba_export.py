import json
import os
import socket
from flask import Flask
import csv

_KEBA_WALLBOX_IP = "***REMOVED***"
_KEBA_WALLBOX_PORT = 7090
_KEBA_WALLBOX_ADDR = (_KEBA_WALLBOX_IP,_KEBA_WALLBOX_PORT)
_KEBA_JSON_FILE = "c-keba.json"

app = Flask(__name__)

car_rfids = {
    '0000000000000000' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED***',
    '***REMOVED***' : '***REMOVED*** - Master',
    '34d8ee3100000001' : '***REMOVED***'
}

def data_load():
    with open(_KEBA_JSON_FILE, 'r') as fp:
        return json.load(fp)

def data_save(data):
    os.rename(_KEBA_JSON_FILE,_KEBA_JSON_FILE+".bak")
    with open(_KEBA_JSON_FILE, 'w') as fp:
        json.dump(data, fp, indent=4)

def data_save_csv(history_json):
    data_file = open('c-keba-export.csv', 'w')
    data = history_json['history']

    #print(data.keys())

    count=1
    csv_writer = csv.writer(data_file)
    for r in sorted(data.keys()):
        #print(r)
        if count == 1:
            header = data[str(r)].keys()
            csv_writer.writerow(header)
        csv_writer.writerow(data[str(r)].values())
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
        #print(report)
        report['Car']=car_rfids[report['RFID tag']]
        report.pop('ID')
        cur_sessionid = report['Session ID']
        if cur_sessionid == -1: 
            continue
        data['history']["%d" % cur_sessionid]=report

@app.route('/')
# ‘/’ URL is bound with hello_world() function.
def hello_world():
    return 'Hello World'

@app.route('/update')
def web_update():
    keba_updatereports(sock, data)
    data_save(data)
    return "Reports: %d" % (len(data['history']))

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

    #app.run()