#-*- coding: latin-1 -*-
import shared, threading, check_connection, time, serial, json, ast, logging, csv, smbus2, board, adafruit_max1704x, pytz, os, glob, pickle
import socket, subprocess
from flask import Flask, render_template, request, redirect, url_for, jsonify,render_template_string
from gpiozero import Buzzer, OutputDevice
from multiprocessing import Process
from mpmath.libmp.libmpf import strict_normalize1
from lora_e220 import LoRaE220
from lora_e220 import LoRaE220, print_configuration
from lora_e220_operation_constant import ResponseStatusCode
from datetime import datetime, timedelta
from empfang import empfange_nachricht
from empfang2 import empfang_normal
#from timezonefinder import TimezoneFinder
from check_connection import *
import RPi.GPIO as GPIO
#Variables--------------------------------------------------------------------------------------------------------------
message_path = "nachrichten.json"
base_dir = '/sys/bus/w1/devices/'
DATEI = "nachrichten.json"
last_reload = datetime.now()
TTYD_PORT = 8787
last_action = datetime.now()
TTYD_CMD = ["ttyd", "--writable", "-p", str(TTYD_PORT), "-i", "0.0.0.0", "bash"]
ttyd_process = None
app = Flask(__name__)
#------------------------------Rendering--------------------------------------------------------------------------------
@app.before_request
def count_visit():
    global last_reload
    last_reload = datetime.now()

@app.route('/')
@app.route('/index')
def index():
    clock = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    shared.logger_data = False
    return render_template('index.html',status=shared.fehler,height = shared.hoehe,text=shared.long,strength=shared.setWifiStrength,text2=shared.lat,startzeit_js=clock,battery_level=shared.battery_level,notify = shared.notify,device =shared.send)

@app.route('/new_kontakt')
def new_kontakt():return render_template('new_kontakt.html')

@app.route('/settings')
def settings():
    save_all()
    return render_template('settings.html',freq = shared.current_freq, power=shared.current_power)

@app.route('/check_position')
def check_position():return render_template('cords.html')

@app.route('/wetter')
def wetter(): return render_template("wetter.html",wetterdaten=shared.wetterdaten,startzeit_js=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),status=shared.fehler,state=shared.state)

@app.route('/terminal')
def terminal():
    start_ttyd()
    print(shared.battery_level)
    return render_template("terminal.html", battery_level=shared.battery_level)

@app.route("/mesange", methods=["GET", "POST"])
def mesange():
    auswahl = wert = None
    nachrichten = None
    print(shared.fehler)
    zeilen = []
    return render_template("message.html",optionen=shared.optionen,auswahl=auswahl,status=shared.fehler,wert=wert,nachrichten=nachrichten,zeilen=zeilen, freq = shared.current_freq)

@app.route('/sensoren')
def sensoren():
    if shared.logger_data:
        print(shared.last_file)
        if not shared.last_file == None:
            with open(f"logings/{shared.last_file}", newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                data = list(reader)
        else: data = None
        return render_template('sensor.html', sensor_data=shared.sensor_data, datatime=shared.time_data,
                               logger_active=shared.logger_service, logger_data_check=shared.logger_data2, data = data)
    else:return render_template('sensor.html', sensor_data=shared.sensor_data, datatime=shared.time_data,
                               logger_active=shared.logger_service, logger_data_check=shared.logger_data2, data = None)

#Routen-----------------------------------------------------------------------------------------------------------------
@app.route('/check_message')
def check_message():
    if os.path.exists(message_path):
        with open(message_path, "r", encoding="utf-8") as fg:
            datas = json.load(fg)
    else:datas = {}
    zeilen = []
    for key, eintrag2 in datas.items():
        if isinstance(eintrag2, dict):
            zeilen.append((
                eintrag2.get("name", "Unbekannt"),
                eintrag2.get("nachricht", ""),
                eintrag2.get("datum", "Unbekannt")
            ))
        else:
            zeilen.append(("Unbekannt", str(eintrag2)))
    nachricht = shared.nachricht
    html_tabelle = render_template_string('''
        {% for name, nachricht, datum in zeilen %}
        <tr>
          <td>{{ name }}</td>
          <td>{{ nachricht }}</td>
          <td>{{ datum }}</td>
        </tr>
        {% endfor %}
    ''', zeilen=zeilen)
    return jsonify({"nachricht": nachricht, "tabelle": html_tabelle})

@app.route('/set_frequenz', methods=['POST'])
def set_frequenz():
    auswahl = request.form.get('auswahl')
    if not auswahl:
        return "Keine Auswahl getroffen!", 400
    state = change_frequenz(auswahl)
    if not state:
        auswahl = "Fehler beim Schreiben"
        return f'<h2><em>{auswahl}</em></h2><a href="{url_for("settings")}">Zurück</a>'
    else: return redirect(url_for('settings'))

@app.route('/battery')
def battery():
    try:
        battery = shared.battery_level
        level = battery.percent if battery else -10
    except Exception:
        level = -10
    return jsonify({'level': int(level)})

@app.route('/show_data')
def show_data():
    shared.logger_data2 = True
    return redirect(url_for('sensoren'))

@app.route('/set_strengh', methods=['POST'])
def set_strengh():
    strengh = request.form.get('strengh')
    if not strengh: return "Keine Auswahl getroffen!", 400
    else:
        state = change_power(strengh)
        if not state:
            strengh = "Fehler beim Schreiben"
            return f'<h2><em>{strengh}</em></h2><a href="{url_for("settings")}">Zurück</a>'
        else: return redirect(url_for('settings'))

@app.route('/set_skala', methods=['POST'])
def set_skala():
    skala = request.form.get('skalen')
    if not skala:
        return "Keine Auswahl getroffen!", 400
    else:
        state = change_skalen(skala)
        if not state:
            state = "Fehler beim ändern"
            return f"<h2><em>{skala}</em></h2><a href='{url_for('settings')}'>Zurück</a>"
        else:
            return redirect(url_for('settings'))

@app.route('/check_sensors2')
def check_sensors2():
    check_sensors()
    return 200

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.get_json()
    if data:
        lat = data.get('latitude')
        lon = data.get('longitude')
        accuracy = data.get('accuracy')
        height = data.get('altitude')
        height_accuracy = data.get('altitudeAccuracy')
        print(f"Empfangene Koordinaten: {lat}, {lon} (Genauigkeit: {accuracy}m),höhen genauigkeit:{height_accuracy}, höhe:{height}")
        shared.hoehe = height
      #  tf = TimezoneFinder(in_memory=True)
       # tz = tf.timezone_at(lng=lon, lat=lat)
       # shared.long = lon
        #shared.lat = lat
      #  print("Zeitzone:", tz)
       # berlin_tz = pytz.timezone(tz)
        #berlin_jetzt = datetime.now(berlin_tz)
        #print(f"Berlin: {berlin_jetzt}")
        #try:
         #   subprocess.run(["sudo", "date", "--set", message], check=True, capture_output=True, text=True)
          #  return 0
        #except Exception as e:
         #   if hasattr(e, "stderr") and e.stderr:
          #      return e.stderr.strip()
           # else:
            #    return str(e)
        return redirect("/index")
    return 'Keine Daten erhalten', 400

@app.route('/check_sensors')
def check_sensors():
    print("Temperatur wird gecheckt")
    check_sensoren()
    return jsonify({'status': 'ok'})

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('feld1')
    adress = request.form.get('feld2')
    print(f"Name: {name}")
    print(f"ID: {adress}")
    send_kontakt(name,adress)
    return redirect("/mesange")

@app.route("/status")
def get_status(): return{"status": shared.shared_data.get("status", "")}

@app.route("/toggle", methods=["POST"])
def toggle():
    state = request.get_json().get("state", False)  # True oder False
    return jsonify(success=True, state=state)

@app.route("/daten")
def daten(): return jsonify(shared.wetterdaten)

@app.route("/upcl", methods=["POST"])
def upcl():
    msg = clock_update()
    if msg == 0: msg = "Fertig"
    return jsonify({"message": msg})

def lade(datei):
    if os.path.exists(datei):
        with open(datei, "r", encoding="utf-8") as fe:
            return json.load(fe)
    return {}

@app.route("/st_logger", methods=["POST"])
def st_logger():
    minuten = request.form.get("minuten")
    file_name = request.form.get("file_name")
    file_name= str(file_name) + ".csv"
    if shared.logger_service:
        a , b = shared.logger_data
        shared.last_file = b
        shared.logger_service = False
        shared.header.clear()
        shared.sensor_data.clear()
    else:
        shared.logger_data = [minuten, file_name]
        shared.logger_service = True
    return redirect(url_for('sensoren'))

@app.route("/send_message", methods=["POST"])
def send_message():
    shared.fehler = ""
    option = request.form.get("optionen")
    neue_option = request.form.get("neue_option")
    if shared.ser == "404":
        shared.fehler = 404
    else:
        status = mes_senden(option, neue_option)
        if not status:
            print(f"Hat nicht geklappt")
            shared.fehler = 404
    return redirect("/mesange")

@app.route('/notify-closed', methods=['POST'])
def notify_closed():
    shared.notify = False
    return jsonify(success=True)

@app.route("/check-updates")
def check_updates():return jsonify(notify = shared.notify,device =shared.send)

@app.route("/request_kontakt", methods=["GET", "POST"])
def request_kontakt():
    if request.method == "POST":
        text = request.form.get("eingabe", "")
        action = request.form.get("action")
        result = None
        if action == "annehmen":
            result = 1
        elif action == "ablehnen":
            return redirect("/mesange")
        print(f"Eingabe: {text}, Ergebnis: {result}")
        return jsonify({"ergebnis": result, "eingabe": text})
    return render_template("quest_kontakt.html")

#Initalisierung und main Thread-----------------------------------------------------------------------------------------

def is_port_in_use(port):
    """Prüft, ob ein Port bereits belegt ist."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) == 0

def start_ttyd():
    global ttyd_process
    if not is_port_in_use(TTYD_PORT):
        ttyd_process = subprocess.Popen(TTYD_CMD)
        # kurze Pause, damit ttyd starten kann
        time.sleep(1)
        print(f"ttyd gestartet auf Port {TTYD_PORT}")
    else:
        print(f"ttyd läuft bereits auf Port {TTYD_PORT}")

def check_battery():
    voltage = round(shared.max17048.cell_voltage, 2)
    shared.battery_level = round(shared.max17048.cell_percent, 1)
    shared.battery_level= shared.battery_level + 5
    print(f"Spannung: {voltage:.2f} V, Ladezustand: {shared.battery_level:.1f} %")
    if shared.battery_level == 0.0:
        print(f"Spannung: {shared.battery_level:.1f} %")
    elif shared.battery_level < 5:
        print("to low battery please shutdown")
        #os.system("sudo shutdown -h now")


def e220_check():
    try:
        uart = serial.Serial(port="/dev/serial0",baudrate=9600, timeout=1)
        lora = LoRaE220('900T22D', uart)
        code = lora.begin()
        print("Init-Antwort:", ResponseStatusCode.get_description(code))
        if code == ResponseStatusCode.SUCCESS:return True
        else:return False
    except Exception as e:
        print(f"Fehler beim Zugriff auf E220: {e}")
        return False

def check_max17048(addr, bus):
    try:
        bus.read_byte(addr)
        return True
    except OSError:
        return False


def init_hardware():
    global buzzer, powerp
    try:
        buzzer = Buzzer(16)
    except Exception as e:
        print(f"Buzzer konnte nicht initialisiert werden: {e}")
        buzzer = None
    try:
        powerp = OutputDevice(13)
    except Exception as e:
        print(f"Power konnte nicht initialisiert werden: {e}")
        powerp = None
    print("Power wurde angeschaltet")
    powerp.on()
    i2c_bus = 1
    device_adress = 0x36
    shared.bus = smbus2.SMBus(i2c_bus)
    if check_max17048(device_adress, shared.bus):
        print("MAX17048 erkannt und antwortet auf I2C-Adresse 0x36!")
        shared.i2c = board.I2C()  # SCL, SDA
        shared.max17048 = adafruit_max1704x.MAX17048(shared.i2c)
        check_battery()
    else:
        shared.battery_level = -10
        shared.fehler += "Battery Ladestand konnte nicht gelesen werden"
    if e220_check():
        print("Es funktioniert")
        time.sleep(0.1)
        shared.ser = serial.Serial(port='/dev/serial0', baudrate=9600, timeout=1)
        shared.lora = LoRaE220('900T22D', shared.ser, aux_pin=shared.aux_pin, m0_pin=shared.M0_PIN, m1_pin=shared.M1_PIN)
        time.sleep(1)
        code = shared.lora.begin()
        if code == 1:
            for i in range(3):
                try:
                    code, configuration = shared.lora.get_configuration()
                    print("ADDH:", hex(configuration.ADDH))
                    print("ADDL:", hex(configuration.ADDL))
                    shared.ADDH = configuration.ADDH
                    shared.ADDL = configuration.ADDL
                    break
                except Exception as e:
                    print("Fehler:", e)
                    print("Versuch", i + 1, "von", 3)
                    if i == 3 - 1: exit()
            threading.Thread(target=manager2, daemon=False).start()
        else:
            print("?Fehler beim Starten von Lora")
            shared.fehler += "Funksystem konnte nicht gestartet werden, Funk deaktiviert"
            shared.current_freq = -10
            shared.current_power = -10
            shared.fehler2 += "1"
    else: return "404"

def manager2():
    global last_reload, last_action
    print("manager2 gestartet")
    count =0
    while True:
        if shared.manager_check == 0:
            shared.thread_wait = False
            count = count + 1
            print(count)
            message, server_id = empfang_normal(shared.myid)
            print(f"mes:{message}, ser:{server_id}, manager2")
            if not message == "404" or None:check_connection.auswertung(message, server_id)
            if count >= 30 and shared.battery_level != 0 and shared.battery_level!= -10 or shared.battery_level ==0.0:
                print("check_battery")
                count = 0
                check_battery()
            if shared.notify2:
                shared.notify2 = False
                thread2 = threading.Thread(target=sound, daemon=True)
                thread2.start()
        else:
            shared.thread_wait = True
        if shared.logger_service:
            a, b = shared.logger_data
            if datetime.now() - last_action > timedelta(minutes=int(a)):
                sensor_logger(b)
                last_action = datetime.now()
def sound():
    buzzer.on()
    time.sleep(1)
    buzzer.off()

def save_all():
    variablen = {
        "skalas": shared.skalas,
        "sensors": shared.sensors,
        "current_power": shared.current_power,
        "current_freq": shared.current_freq,
    }
    with open("variablen.pkl", "wb") as f:
        pickle.dump(variablen, f)
    print("Alles wichtige wurde gespeichert")

def load_file():
    print("variablen werden geladen")
    with open("variablen.pkl", "rb") as f:
        geladene_variablen = pickle.load(f)
    # Alle Variablen ins shared-Modul schreiben
    for name, wert in geladene_variablen.items():
        setattr(shared, name, wert)


if __name__ == '__main__':
    if os.path.exists('variablen.pkl'):
        load_file()
    shared.ser = init_hardware()
    sound()
    if os.path.exists('kontakt.csv'):
         with open("kontakt.csv", "r", encoding="utf-8") as f: shared.kontakte = list(csv.reader(f))
         print(shared.kontakte)
         for eintrag in shared.kontakte:
             if len(eintrag) > 2: shared.optionen[eintrag[0]] = eintrag[len(eintrag) // 2]
    else:
        print(f"Keine Kontakte:SAD SMILE")
    #logging.getLogger('werkzeug').disabled = True
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
