#-*- coding: latin-1 -*-
import time, ast, os, pytz, csv, app, shared, json, board, busio, smbus2, adafruit_max1704x, glob, csv
from adafruit_bme280 import basic as adafruit_bme280
from multiprocessing import Process, Event
from lora_e220 import LoRaE220, TransmissionPower
from lora_e220_operation_constant import ResponseStatusCode
import RPi.GPIO as GPIO
from send import senden
from datetime import datetime
from empfang import empfange_nachricht
emp_id = ""
temperature = None
humidity = None
pressure = None
logger = None
stop_event = None
altitude = None
celsius = True
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
        print("ich bin hier")
        teil1, teil2 = message.split(".")
        print(f"{teil1}.{teil2}")
        if teil2 == "4":
            mes_empfangen(teil1)
        elif teil2 == "3":
            clock_update()
        elif teil2 == "5":
            emp_new_kontakt(teil1)
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


def server_anfrage(s_id, number):
    print(f"Server wird angefragt: s_id={s_id}, number={number}")

    # Anfrage senden
    manager(1, s_id, f"{shared.myid}.{number}")
    print("Warte auf Antwort...")
    print(datetime.now())

    # Antwort empfangen
    message, server_id = manager(2, shared.myid, "")
    print(f"Antwort erhalten: message={message}, server_id={server_id}")

    # Fehlerbehandlung
    if not message or message == "404" or server_id == "404":
        print("Fehler: Keine gültige Antwort vom Server erhalten.")
        return "404", "404"

    # Erfolg
    shared.server_id = server_id
    return message, server_id


def emp_new_kontakt(device_id):
    print("Empfange Kontakt")
    print(device_id)
    shared.manager_check = 2
    time.sleep(1)
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
    key, value = message.split(":")
    print(key)  # Temperatur
    print(value)  # 25.3
    shared.manager_check = 0
    save_kontakt(key, value)

def send_kontakt(name,ziel):
    print("Kontakt wird angefragt")
    print(f"ziel:{ziel}")
    shared.manager_check = 2
    time.sleep(1)
    t, idk = server_anfrage(ziel, 5)
    print(t)
    if t != "1":
        print("Server antwortet nicht.")
        print(datetime.now())
        shared.manager_check = 0
        return False
    manager(1, ziel,f"{shared.myname}:{shared.myid}")
    message, empid = manager(2, shared.myid, "")
    if message == "1":
        print("Hat geklappt")
        shared.manager_check = 0
        save_kontakt(name,ziel)
    else:
        print("Fetter Fehker")
        shared.manager_check = 0
        return False


def save_kontakt(name, nummer):
    print(f"Erstelle neuen Kontakt: {name}, {nummer}")
    neue_zeile = [name, "", nummer]
    with open("kontakt.csv", "a", newline="") as datei:
        writer = csv.writer(datei)
        writer.writerow(neue_zeile)
    print("Neue Zeile wurde hinzugefügt!")


def get_last_number(kontakte, name):
    if name is None:return None
    target = name.strip().lower()
    for kontakt in kontakte:
        if kontakt and kontakt[0].strip().lower() == target:return kontakt[-1]  # letzter Wert der gefundenden Unterliste
    return None

# I think kann gelöscht werden!!!!
#def check_server():
#    print("Versuche irgendtwie Server/Device zu erreichen")
#    manager(1,0,"40")
#    t, idk = manager(2,shared.myid,"")
#    if t == "10":
#        print("Geklappt")
 #       print(idk)
  #      return idk
   # else:
    #    print("Fehler")
     #   return shared.fehler


def finde_ersten_wert(datei, zielwert):
    with open(datei, "r", encoding="utf-8") as f:
        kontakte = list(csv.reader(f))
    for eintrag in kontakte:
        # Prüfen, ob Zeile mindestens 2 Spalten hat
        if len(eintrag) >= 2:
            # Prüfen, ob der Zielwert in der letzten Spalte steht
            if eintrag[-1] == zielwert:
                return eintrag[0]
    # Wenn nichts gefunden wird
    return None


def speichern(id3, nachricht, datei):
    name = finde_ersten_wert("kontakt.csv", id3)
    if name:print(f"Gefunden! Erste Spalte: {name}")
    else:
        print("Nicht in Kontakten vorhanden")
        name = "Unbekannt"
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

def mes_empfangen(sender_id):
    print("Starte Empfang...")
    shared.manager_check = 2
    time.sleep(1)
    manager(1, sender_id, "1")
    nachricht = ""
    fcount = 0
    while True:
        time.sleep(1)
        print("Empfange Message")
        message, empid = manager(2, shared.myid, "")
        print(f"sender_id:{sender_id}")
        print(f"Empfangen: {message}")
        if not message or ":" not in message or message == "404":
            print("Ungültige Nachricht, warte...")
            manager(1, sender_id, "2")
            fcount = fcount + 1
            continue
        if fcount >= 3:break
        schluessel, wert = message.split(":", 1)
        nachricht += wert
        print(f"message: {message}, wert: {wert}, schluessel: {schluessel}")
        if schluessel == "end":
            speichern(sender_id, nachricht, "nachrichten.json")
            time.sleep(0.5)
            manager(1, sender_id, "1")
            shared.nachricht = nachricht
            shared.manager_check = 0
            break
        else:manager(1, sender_id, "1")

def mes_senden(option, text):
    shared.manager_check = 2
    time.sleep(1)
    ziel = get_last_number(shared.kontakte, option)
    if not ziel:
        print("Kein Ziel gefunden.")
        return False
    print(f"zieladresse:{ziel}")
    t, idk = server_anfrage(ziel,4)
    if t != "1":
        print("Server antwortet nicht.")
        shared.manager_check = 0
        return False
    print(f"Server antwortet: {idk}, starte nachrichten übermittlung")
    teile = [text[i:i+12] for i in range(0, len(text), 12)]
    print(f"text:{text}, teile:{teile}")
    for i, t in enumerate(teile):
        teil_id = "end" if i == len(teile) - 1 else str(i)
        nachricht = f"{teil_id}:{t}"
        print(f"Sende: {nachricht}")
        antwort = send_mes(nachricht, ziel)
        if antwort == 1 or antwort == "1":
            print(f"Teil {i + 1}/{len(teile)} erfolgreich gesendet.")
            continue
        elif antwort == "2":
            print("Abbruch")
            return False
        else:
            print("unbekannte antowrt ")
            break
    shared.manager_check = 0
    speichern(shared.myid, text,"nachrichten.json")
    return True

def send_mes(nachricht, ziel):
    print("Nachricht wird gesendet:", nachricht)
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
            if count == 1:senden(id2, text)
            elif count == 2:
                message, server_id = empfange_nachricht(shared.myid)
                print(datetime.now())
                print(f"Nachricht Empfangem.Message: {message},server_id:{server_id}")
                return message, server_id
            elif count == 0:
                if not shared.manager_check == 2:shared.manager_check = 0
            count = 0

def change_frequenz(channel):
    shared.manager_check = 2
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
    val = 99
    shared.manager_check = 2
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
    time.sleep(1)
    status, conf2 = shared.lora.get_configuration()
    if status != 1:return False
    if conf2.OPTION.transmissionPower == val:
        shared.current_power = int(power_dbm)
        shared.manager_check = 0
        print(f"Erfolgreich gesetzt auf:{conf2.OPTION.transmissionPower}")
        return True
    else:return False

#-----------------------Angeschlossene Sensoren-------------------------------------------------------------------------

def check_sensoren():
    print("Es werden angeschlossene Sensoren geprüft")
    if not check_one_wire(): shared.temp_c = 0
    if not restart_i2c(1): return False, False, False
    check_i2c_devices(shared.sensors)
    if shared.logger_service:
        sensor = read_sensors()
        return sensor
    else:
        read_sensors()


def read_sensors():
    global temperature, humidity, pressure, altitude
    if "BME280" in shared.SENSOREN:
        if shared.logger_service:
            shared.sensor_data.update({
                "Luftfeuchtigkeit": f"{round(shared.bme280.humidity, 1)} %",
                "Luftdruck": f"{round(shared.bme280.pressure, 1)} hPa",
                "Temperatur": f"{round(shared.bme280.temperature, 1)} °C"
            })
            return shared.sensor_data
        else:

            temperature = round(shared.bme280.temperature, 1)
            humidity = round(shared.bme280.humidity, 1)
            pressure = round(shared.bme280.pressure, 1)
            altitude = round(shared.bme280.altitude, 1)
            if not shared.celsius: shared.sensor_data["Temperatur"] = f"{(temperature * 9/5) + 32:.2f} °F"
            else: shared.sensor_data["Temperatur"] = f"{temperature} °C"
            shared.sensor_data["Luftfeuchtigkeit"] =f"{humidity} %"
            shared.sensor_data["Luftdruck"] = f"{pressure} hPa"
            shared.sensor_data["Altitude"] = f"{altitude} meters"
            print("Daten der Sensoren werden gelesen")
            print("Temperature: %0.1f C" % temperature)
            print("Humidity: %0.1f %%" % humidity)
            print("absolute Pressure: %0.1f hPa" % pressure)
            print("Altitude = %0.2f meters" % altitude)
            print(shared.sensor_data)
    temp_c = round(shared.temp_c, 1)
    if shared.temp_c != 0:
        if shared.celsius:
            shared.sensor_data["Temp_one"] = f"{temp_c} °C"
        else:
            shared.sensor_data["Temp_one"] = f"{(temp_c * 9/5) + 32:.2f} °F"
    shared.time_data = datetime.now().strftime("%H:%M")

def check_i2c_devices(sensor_list, bus_id=1):
    shared.i2c = board.I2C()
    print("? I²C-Geräte-Check:")
    for name, address in sensor_list:
        try:
            shared.bus.read_byte(address)
            print(f"{name} antwortet auf Adresse {hex(address)}")
            if address == 0x36:
                shared.max17048 = adafruit_max1704x.MAX17048(shared.i2c)
                shared.SENSOREN.append("MAX17048")
            if address == 0x76:
                shared.bme280 = adafruit_bme280.Adafruit_BME280_I2C(shared.i2c, address=0x76)
                shared.bme280.mode = adafruit_bme280.MODE_NORMAL
                shared.SENSOREN.append("BME280")
        except OSError:
            print(f"{name} antwortet NICHT auf Adresse {hex(address)}")
            if address == 0x36: shared.battery_level = -10

def restart_i2c(bus_id=1):
    try:
        shared.bus.close()
        time.sleep(0.5)
        shared.bus = smbus2.SMBus(bus_id)
        return True
    except Exception as e: return False

def check_one_wire():
    device_folders = glob.glob(base_dir + '28-*')
    if not device_folders:
        print("? Kein 1-Wire-Sensor gefunden! Bitte Verkabelung prüfen.")
        return False
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

def logger_service(minuten, file_name):
    global logger, stop_event
    print("Startet/stoppt den sensor logger")
    print(f"Wiederholzeit: {minuten}")
    if shared.logger_service:
        print("logger service beenden")
        shared.logger_service = False
        stop_event.set()  # Signal zum Beenden
        logger.join()
        print("beendet")
    else:
        shared.logger_service = True
        stop_event = Event()
        logger = Process(target=sensor_logger, args=(minuten,stop_event,file_name))
        logger.start()


def sensor_logger(minuten, stop_event, file_name):
    print("Sensor logger start")
    seconds = int(minuten) * 60
    daten = [["Luftdruck", "Temperature", "Luftfeuchte", "Uhrzeit"]]
    with open(file_name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(daten)
    t_count = 0
    while not stop_event.is_set():
        if t_count >= seconds:
            print("Speichern")
            sensor = check_sensoren()
            if isinstance(sensor, dict):
                values = [sensor.get("Luftdruck"), sensor.get("Temperatur"), sensor.get("Luftfeuchtigkeit"), datetime.now().strftime("%H:%M")]
            else:
                # Fallback, falls Tuple oder Liste
                values = list(sensor)

            with open(file_name, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(values)
            print("wurde gespeichert")
            print(sensor)
            t_count = 0
        time.sleep(10)
        t_count += 10


