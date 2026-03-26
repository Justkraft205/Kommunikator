#-*- coding: latin-1 -*-
import time, ast, os, pytz, csv, app, shared, json, board, busio, smbus2, adafruit_max1704x, glob, csv
from multiprocessing import Process, Event
from lora_e220 import LoRaE220, TransmissionPower
from i2c_sensoren import *
from i2c_sensoren import restarting_i2c
from lora_e220_operation_constant import ResponseStatusCode
from datetime import datetime
import RPi.GPIO as GPIO
from send import senden
from empfang import empfange_nachricht
emp_id = ""
temperature = None
humidity = None
logger_counter = 0
pressure = None
last_file = None
logger = None
stop_event = None
altitude = None
base_dir = '/sys/bus/w1/devices/'

# Muss neu gemacht werden!!!
def take_wetter():
        count = 0
        message, server = server_anfrage(2)
       # print("aufgerufne")
       # manager(1, 0,f"{shared.myid}.2")
       # message, shared.server_id = manager(2,0 ,"")
        #if message == None:shared.shared_data["status"] = "404"
        #print("Empfangene Nachricht:", message)
        if message == "1":
            manager(1, shared.server_id,f"{shared.cords}.{shared.state}")
            daten = {}
            while count < 5:
                message = manager(2, shared.server_id,"")
             #   daten = convert(message)
                if not isinstance(daten, dict):
                    print("Ungültige Daten empfangen:", daten)
                    continue
                else:count += 1
                shared.wetterdaten = shared.shared_data["wetterdaten"]
                for eintrag in shared.wetterdaten:
                    if eintrag[0] in daten:
                        eintrag[count] = str(daten[eintrag[0]])
                        shared.shared_data["wetterdaten"] = shared.wetterdaten
                        shared.shared_data["status"] = "12"

def auswertung(message, server_id):
        teil1, teil2 = message.split(".")
        print(datetime.now())
        if teil2 == "4":mes_empfangen(teil1, server_id)
        elif teil2 == "3":clock_update()
        elif teil2 == "5":emp_new_kontakt(teil1)
# Muss geändert werden
def clock_update():
    message, shared.server_id= server_anfrage(3)
    if message == "1":manager(1, shared.server_id,f"50.143082;8.586546")
    else: return "404"
    time.sleep(0.5)
    message,idk = manager(2, shared.myid, "")
    try:
        subprocess.run(["sudo", "date", "--set", message],check=True,capture_output=True,text=True)
        return 0
    except Exception as e:
        if hasattr(e, "stderr") and e.stderr: return e.stderr.strip()
        else:return str(e)

def emp_new_kontakt(device_id):
    print("Empfange Kontakt")
    print(device_id)
    shared.manager_check = 2
    while shared.thread_wait == False:
        time.sleep(0.1)
    print(datetime.now())
    print("vor")
    manager(1, device_id,"1")
    print("nach")
    print(datetime.now())
    message, empid = manager(2, shared.myid, "")
    if not message or ":" not in message or message == "404":
        shared.manager_check = 0
        return False
    time.sleep(0.1)
    manager(1, device_id,"1")
    print(f"Empfangen:message: {message}, empid: {empid}")
    key, value, emp_addh,emp_addl = message.split(":")
    print(key)  # Temperatur
    print(value)  # 25.3
    shared.manager_check = 0
    save_kontakt(key, value, emp_addh, emp_addl)

def send_kontakt(name,ziel):
    print("Kontakt wird angefragt")
    print(f"ziel:{ziel}")
    shared.manager_check = 2
    while shared.thread_wait == False: time.sleep(0.1)
    t, idk = server_anfrage(ziel, 5)
    print(t)
    if t != "1":
        print("Server antwortet nicht.")
        print(datetime.now())
        shared.manager_check = 0
        return False
    manager(1, ziel,f"{shared.myname}:{shared.myid}:{shared.ADDH}:{shared.ADDL}")
    message, empid = manager(2, shared.myid, "")
    if message == "1":
        print("Hat geklappt")
        shared.manager_check = 0
        save_kontakt(name,ziel)
    else:
        print("Fetter Fehker")
        shared.manager_check = 0
        return False

def save_kontakt(name, nummer, addh, addl):
    print(f"Erstelle neuen Kontakt: {name}, {nummer}")
    neue_zeile = [name, f"{addh}:{addl}", nummer]
    with open("kontakt.csv", "a", newline="") as datei:
        writer = csv.writer(datei)
        writer.writerow(neue_zeile)
    print("Neue Zeile wurde hinzugefügt!")

def finde_ersten_wert(datei, zid):
    with open(datei, "r", encoding="utf-8") as f:kontakte = list(csv.reader(f))
    if ";" in zid:spalte = 1
    else:spalte = 2
    for eintrag in kontakte:
        if len(eintrag) == 3:
            print(eintrag[spalte])
            if eintrag[spalte] == zid:return eintrag[0]
    return None

def speichern(id3, nachricht, datei):
    name = finde_ersten_wert("kontakt.csv", id3)
    if not name: name = "Unbekannt"
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as f:
            daten = json.load(f)
    else:daten = {}
    datum_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    if daten:naechste_id = max(map(int, daten.keys())) + 1
    else:naechste_id = 1
    daten[str(naechste_id)] = {"name": name,"nachricht": nachricht,"datum": datum_str}
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)
    print(f"Nachricht gespeichert mit ID {naechste_id}")
    shared.send = name
    shared.notify = True
    shared.notify2 = True

def mes_empfangen(sender_id, fixed):
    manager(1, sender_id, "1")
    nachricht = ""
    fcount = 0
    while True:
        message, empid = manager(2, shared.myid, "")
        if not message or ":" not in message or message == "404":
            manager(1, sender_id, "2")
            fcount = fcount + 1
            continue
        if fcount >= 3:break
        schluessel, wert = message.split(":", 1)
        nachricht += wert
        if schluessel == "end":
            speichern(sender_id, nachricht, "nachrichten.json")
            manager(1, sender_id, "1")
            shared.nachricht = nachricht
            break
        else:manager(1 , sender_id, "1")

def get_last_number(kontakte, name):
    if name is None:return None
    target = name.strip().lower()
    for kontakt in kontakte:
        if kontakt and kontakt[0].strip().lower() == target:
            if kontakt[1] is None: shared.fixed_message = False
            if shared.fixed_message:adress = kontakt[1]
            else: adress = kontakt[-1]
            return adress
    return None

def server_anfrage(s_id, number):
    print(f"Server wird angefragt: s_id={s_id}, number={number}")
    if shared.fixed_message:message = f"{shared.ADDH}:{shared.ADDL}.{number}"
    else:message = f"{shared.myid}.{number}"
    print(message)
    manager(1, s_id, message)
    print(f"Warte auf Antwort...:{datetime.now()}")
    message, server_id = manager(2, shared.myid, "")
    print(f"Antwort erhalten: message={message}, server_id={server_id}")
    if not message or message == "404" or server_id == "404":
        print("Fehler: Keine gültige Antwort vom Server erhalten.")
        return "404", "404"
    shared.server_id = server_id
    return message, server_id

def mes_senden(option, text):
    if "1" in shared.fehler2:return False
    shared.manager_check = 2
    c = 0
    while not shared.thread_wait:
        time.sleep(0.1)
        c+=1
        if c >= 101:return False
    id = get_last_number(shared.kontakte, option)
    print(f"ziel: {id}")
    if not id:return False
    t, idk = server_anfrage(id,4)
    if t != "1":
        shared.manager_check = 0
        return False
    teile = [text[i:i+12] for i in range(0, len(text), 12)]
    print(f"text:{text}, teile:{teile}")
    for i, t in enumerate(teile):
        teil_id = "end" if i == len(teile) - 1 else str(i)
        nachricht = f"{teil_id}:{t}"
        print(f"Sende: {nachricht}")
        antwort = send_mes(nachricht, id)
        if antwort == 1 or antwort == "1":
            print(f"Teil {i + 1}/{len(teile)} erfolgreich gesendet.")
            continue
        elif antwort == "2":return False
        else:
            print("unbekannte antowrt ")
            break
    shared.manager_check = 0
    speichern(shared.myid, text,"nachrichten.json")
    return True

def send_mes(nachricht, ziel):
    print(f"Nachricht: {nachricht}, ziel: {ziel}")
    fcount = 0
    while fcount < 3:
        manager(1, ziel, nachricht)
        antwort, _ = manager(2, shared.myid, "")
        print(f"Antwort empfangen: {antwort}")
        if antwort == "1":
            return 1
        elif antwort == "2":
            print("Empfänger fordert Wiederholung an...")
            fcount += 1
        else:
            print("Keine Antwort, versuche erneut...")
            fcount += 1
        time.sleep(1)
    print("Zu viele Fehlversuche ? Abbruch.")
    return 2

def manager(count,id2,text):
    if not shared.fehler == "104":
        if not shared.manager_check == 2: shared.manager_check = 1
        print(f"id:{id2}, text:{text}")
        print(datetime.now())
        for i in range(2):
            if count == 1:
                senden(id2, text, shared.current_freq)
            elif count == 2:
                message, server_id = empfange_nachricht(shared.myid, shared.fixed_message)
                print(datetime.now())
                print(f"Nachricht Empfangem.Message: {message},server_id:{server_id}")
                return message, server_id
            elif count == 0:
                if not shared.manager_check == 2:shared.manager_check = 0
            count = 0
    else:
        print("Wegen fehler abgebrochen")

def change_frequenz(channel):
    if "1" in shared.fehler2:return False
    shared.manager_check = 2
    while shared.thread_wait == False:time.sleep(0.1)
    channel = int(channel)
    status, configuration = shared.lora.get_configuration()
    if not status == 1: return False
    configuration.CHAN = channel
    status, confSet = shared.lora.set_configuration(configuration)
    if not status == 1:return False
    print(f"\n??  Setze neue Frequenz auf Kanal {channel} ({850.125 + channel} MHz)...")
    time.sleep(1)
    status, conf2 = shared.lora.get_configuration()
    if not status == 1: return False
    print(f"CHAN: {conf2.CHAN}")
    if conf2.CHAN == channel:
        shared.current_freq = int(channel)
        shared.manager_check = 0
        return True
    else:return False

def change_power(power_dbm):
    shared.manager_check = 2
    while shared.thread_wait == False:time.sleep(0.1)
    print(f"?? Ändere Sendeleistung auf {power_dbm} dBm")
    if power_dbm == "22": val = 0
    elif power_dbm == "17": val = 1
    elif power_dbm == "13": val = 2
    elif power_dbm == "10": val = 3
    else:return False
    status, conf = shared.lora.get_configuration()
    if status != 1:return False
    conf.OPTION.transmissionPower = val
    status, _ = shared.lora.set_configuration(conf)
    if status != 1:return False
    time.sleep(0.1)
    status, conf2 = shared.lora.get_configuration()
    if status != 1:return False
    if conf2.OPTION.transmissionPower == val:
        shared.current_power = int(power_dbm)
        shared.manager_check = 0
        print(f"Erfolgreich gesetzt auf:{conf2.OPTION.transmissionPower}")
        return True
    else:return False

def change_skalen():
    print("Hi")

#-----------------------Angeschlossene Sensoren-------------------------------------------------------------------------

def check_sensoren():
    print("Es werden angeschlossene Sensoren geprüft")
    t = restarting_i2c()
    if not t: print("Error")
    sensoren =check_i2c_devices(shared.sensors)
    print("ich bin stuck")
    ok = read_sensors(sensoren)
    if not ok: print("Fehler beim sensor lesen")
    shared.time_data = datetime.now().strftime("%H:%M")
    #if not check_one_wire(): shared.temp_c = 0
    #if not restart_i2c(1): return False, False, False
    #check_i2c_devices(shared.sensors)
    #if shared.logger_service:
     #   sensor = read_sensors()
      #  print(f"check_sensor hat als rückgabe:{sensor}")
       # return sensor
   # else:
    #    t= read_sensors()
     #   if not t: print("Error")


#def read_sensors():
 #   global temperature, humidity, pressure, altitude
  #  teile = shared.skalas.split(",")
   # shared.sensor_data = {}
    #if "BME280" in shared.SENSOREN:
      #  x = round(shared.bme280.humidity, 1)
     #   y = round(shared.bme280.pressure, 1)
    #    z = round(shared.bme280.temperature, 1)
     #   print(dir(shared.bme280))
     #   shared.sensor_data.update({
      #      "Luftfeuchtigkeit": f"{eval(teile[5])} {teile[4]}",
       #     "Luftdruck": f"{eval(teile[3])} {teile[2]}",
        #    "Temperatur": f"{eval(teile[1])} {teile[0]}"
       # })
    #z = round(shared.temp_c, 1)
    #if z != 0: shared.sensor_data["Temp_one"] = f"{eval(teile[1])} {teile[0]}"
    #shared.time_data = datetime.now().strftime("%H:%M")
    #return True


def check_one_wire():
    device_folders = glob.glob(base_dir + '28-*')
    if not device_folders: return False
    device_folder = device_folders[0]
    shared.device_file = device_folder + '/w1_slave'
    try:
        shared.temp_c, shared.temp_f = read_temp()
        if celsius:
            print(f"Temperatur: {shared.temp_c:.2f} °C")
            return True
        else:
            print(f"{shared.temp_f:.2f} °F")
    except FileNotFoundError:
        print("?? Sensor getrennt oder nicht erkannt.")
    except Exception as e:
        print(f"Fehler beim Lesen: {e}")
    time.sleep(2)


def read_temp_raw():
    with open(shared.device_file, 'r') as f:
        return f.readlines()

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

def sensor_logger(file_name):
    global logger_counter
    logger_counter += 1
    print("Speichern")
    check_sensoren()
    if logger_counter == 1:
        header = shared.header + ["Uhrzeit"]
        with open(f"logings/{file_name}", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(header)
    print("logger hat als rückgabe:", shared.sensor_data)
    if isinstance(shared.sensor_data, dict):
        values = [shared.sensor_data.get(k) for k in shared.header]
        values.append(datetime.now().strftime("%H:%M"))
    else:
        values = list(shared.sensor_data)
    with open(f"logings/{file_name}", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(values)
    shared.sensor_data.clear()
    print("wurde gespeichert")

