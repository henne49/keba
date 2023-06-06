import json
import os
import socket
import csv
import datetime
import time
from flask import Flask, send_file, render_template
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

_KEBA_WALLBOX_IP = os.environ['KEBA_WALLBOX_IP']
_KEBA_WALLBOX_PORT = int(os.environ['KEBA_WALLBOX_PORT'])
_ENERGY_PRICE = float(os.environ['ENERGY_PRICE'])
_KEBA_WALLBOX_ADDR = (_KEBA_WALLBOX_IP, _KEBA_WALLBOX_PORT)

_KEBA_JSON_TEMPLATE_FILE = "template.json"
_KEBA_CSV_FILE = "c-keba-export.csv"
_KEBA_COMPANYCAR_CSV_FILE = "CompanyCar-keba-export.csv"
if __name__ == "__main__":
    _KEBA_CAR_RFIDS = "rfids.json"
    _KEBA_JSON_FILE = "c-keba.json"
else:
    _KEBA_CAR_RFIDS = "data/rfids.json"
    _KEBA_JSON_FILE = "data/c-keba.json"
_COMPANYCAR = os.environ['COMPANYCAR']


def rfid_load():
    global car_rfids
    if os.path.exists(_KEBA_CAR_RFIDS):
        with open(_KEBA_CAR_RFIDS, 'r') as fp:
            car_rfids = json.load(fp)
    else:
        car_rfids = {}


def data_load():
    if os.path.exists(_KEBA_JSON_FILE):
        with open(_KEBA_JSON_FILE, 'r') as fp:
            return json.load(fp)
    else:
        os.popen("cp " + _KEBA_JSON_TEMPLATE_FILE + " " + _KEBA_JSON_FILE)
        with open(_KEBA_JSON_FILE, 'r') as fp:
            return json.load(fp)


def data_save(data):
    os.rename(_KEBA_JSON_FILE, _KEBA_JSON_FILE+".bak")
    with open(_KEBA_JSON_FILE, 'w') as fp:
        json.dump(data, fp, indent=4)


def data_save_csv(history_json):
    global table_headings
    global table_data

    data_file = open(_KEBA_CSV_FILE, 'w')
    data_file_CompanyCar = open(_KEBA_COMPANYCAR_CSV_FILE, 'w')
    data = history_json['history']
    data_CompanyCar = data = history_json['history'].copy()
    count = 1
    csv_writer = csv.writer(data_file, dialect='excel', delimiter=';')
    csv_writer_CompanyCar = csv.writer(
        data_file_CompanyCar, dialect='excel', delimiter=';')

    # print(sorted(data.keys(),key=int), reverse=True)
    for r in sorted(data.keys(), key=int, reverse=True):
        if count == 1:
            header = data[str(r)].keys()
            table_headings = header
            csv_writer.writerow(header)
            table_data = []
        csv_writer.writerow(data[str(r)].values())
        if int(data[str(r)]['E pres']) > 200:
            table_data.append(data[str(r)].values())
        count += 1
    count = 1
    for r in sorted(data.keys(), key=int, reverse=True):
        if count == 1:
            header_CompanyCar = data_CompanyCar[str(r)].keys()
            csv_writer_CompanyCar.writerow(header_CompanyCar)
        # Write in CSV File for CompanyCar
        if (int(data_CompanyCar[str(r)]['E pres']) > 200) and (_COMPANYCAR in data_CompanyCar[str(r)]['Car']):
            csv_writer_CompanyCar.writerow(data_CompanyCar[str(r)].values())
        count += 1
    # table_data.sort(key=lambda x: x[0]['Session ID'], reverse=True)


def init_socket():
    # Create a UDP socket and bind to ANY
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('0.0.0.0', _KEBA_WALLBOX_PORT)
    sock.bind(server_address)
    return sock


def keba_recv(sock):
    while True:
        payload, address = sock.recvfrom(4096)
        if payload.startswith(b"{'E pres':"):
            continue
        if payload.startswith(b"{'Plug': "):
            continue
        if payload.startswith(b"{'Max curr': 0}"):
            continue
        if payload.startswith(b"{'Enable sys': 0}"):
            continue
        if payload.startswith(b"{'State': "):
            continue
        # suspress live updates as long we can't consume them
        break
    return (payload, address)


def keba_sendto(sock, msg):
    sock.sendto(msg.encode('utf-8'), _KEBA_WALLBOX_ADDR)
    data, address = keba_recv(sock)
    return data.decode('utf-8')


def close_socket(sock):
    sock.close()


def keba_getversion(sock):
    return keba_sendto(sock, "i")

def keba_settime(sock, time):
    return keba_sendto(sock, f"setdatetime {time}" )

def keba_getreport(sock, id):
    send_data = "report %d" % id
    return json.loads(keba_sendto(sock, send_data))


def keba_report1(sock):
    send_data = "report 1"
    return json.loads(keba_sendto(sock, send_data))

def keba_report2(sock):
    send_data = "report 2"
    return json.loads(keba_sendto(sock, send_data))

def keba_report3(sock):
    send_data = "report 3"
    return json.loads(keba_sendto(sock, send_data))

def keba_current_charge(sock):
    return keba_report3(sock)['E pres']

def keba_status_ntp(sock):
    match keba_report1(sock)['timeQ']:
        case 0:
            return "No time quality. Clock was never set"
        case 1:
            return "Clock was set but not really synchronized"
        case 2:
            return "Clock was synchronized using an unreliable source"
        case 3:
            return "Clock was synchronized using a reliable source (NTP, OCPP, etc.)"
        case _any:
            return "ERROR"
def keba_status_wallbox(sock):
    match keba_report2(sock)['State']:
        case 0:
            return "Startup"
        case 1:
            return "Not ready for charging Charging station is not connected to a vehicle, is locked by the authorization function or another mechanism"
        case 2:
            return "Ready for charging and waiting for reaction from vehicle"
        case 3:
            return "Charging"
        case 4:
            return "Error is present"
        case 5:
            return "Charging process temporarily interrupted"
        case _any:
            return "ERROR"

def keba_updatereports(sock, data):
    """updates data dict with latest reports"""
    global car_rfids
    for r in range(101, 131):
        report = keba_getreport(sock, r)
        print(report)
        try:
            report['Car'] = car_rfids[report['RFID tag']]
        except:
            report['Car'] = 'unknown'

        report.pop('Curr HW')
        report.pop('started[s]')
        report.pop('ended[s]')
        report.pop('reason')
        report.pop('timeQ')
        report.pop('RFID tag')
        report.pop('RFID class')
        report.pop('Sec')

        energy = int(report['E pres']) / 10000
        report['Energy in kWh'] = str(round(energy, 2)).replace('.', ',')
        report['Price in Euro'] = str(
            round(energy * _ENERGY_PRICE, 2)).replace('.', ',')
        try:
            report['Year'] = datetime.datetime.strptime(
                report['ended'], '%Y-%m-%d %H:%M:%S.%f').year
        except:
            report['Year'] = 0
        try:
            report['Month'] = datetime.datetime.strptime(
                report['ended'], '%Y-%m-%d %H:%M:%S.%f').month
        except:
            report['Month'] = 0
        #print(report)
        report.pop('ID')
        cur_sessionid = report['Session ID']
        if cur_sessionid == -1:
            continue
        data['history']["%d" % cur_sessionid] = report

# Sending the file to the user


@app.route('/download')
def download():
    return send_file(_KEBA_CSV_FILE, as_attachment=True)


@app.route('/downloadCompanyCar')
def downloadCompanyCar():
    return send_file(_KEBA_COMPANYCAR_CSV_FILE, as_attachment=True)


@app.route('/downloadJson')
def downloadJson():
    return send_file(_KEBA_JSON_FILE, as_attachment=True)

@app.route('/setTime')
def setTime():
    print('Init Socket')
    sock = init_socket()
    result = keba_settime(sock,time.time())
    close_socket(sock)
    return result

@app.route('/table')
def table():
    global table_data
    global table_headings
    return render_template("table.html", headings=table_headings, data=table_data)
# https://www.youtube.com/watch?v=mCy52I4exTU


@app.route('/update')
def web_update():
    global data
    print('Init Socket')
    sock = init_socket()
    data = data_load()
    rfid_load()
    keba_updatereports(sock, data)
    data_save(data)
    data_save_csv(data)
    close_socket(sock)
    output = "Reports: %d" % (len(data['history']))
    output = output + '<br><a href="./">Back</a>'

    return output

# ‘/’ URL is bound with Keba Version


@app.route('/')
def startpage():
    global keba_ver
    sock = init_socket()
    keba_ver = keba_getversion(sock)
    data = data_load()
    rfid_load()
    keba_updatereports(sock, data)
   
    status_ntp=keba_status_ntp(sock)
    status_wallbox=keba_status_wallbox(sock)
    charging_status=keba_current_charge(sock)
    data_save(data)
    data_save_csv(data)
    close_socket(sock)
    output = "<p>Keba Report Downloader</p>"
    output = output + f"Keba Wallbox version: {keba_ver}"
    output = output + "<br>" + f"{status_ntp}"
    output = output + "<br>" + f"{status_wallbox}"
    if status_wallbox == "Charging" :
        output = output + "<br> Charged Energy: " +f"{round(charging_status/10000,2)}" +" kWh"
    output = output + "<br>Reports: %d" % (len(data['history']))
    output = output + '<br><a href="./download">Download Full</a>'
    output = output + '<br><a href="./downloadCompanyCar">Download CompanyCar</a>'
    output = output + '<br><a href="./downloadJson">Download JSON File</a>'
    output = output + '<br><a href="./update">Update</a>'
    if status_ntp == "No time quality. Clock was never set" :
        output = output + '<br><a href="./setTime">Sync Browser Time</a>'
    output = output + '<br><a href="./table">Show Table</a>'
    return output

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5050,debug=True)
    print (__name__)