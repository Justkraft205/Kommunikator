battery_level = 0
setWifiStrength = 2  # 0 bis 4
fehler = ""
current_power = 13
current_freq = 18
temp_f = 0
temp_c = 0
wert = ""
M1_PIN = 27
M0_PIN = 17
aux_pin = 22
lora = None
sensor_data = {}
kontakte = []
send = ""
bus = None
bme280 = None
i2c = None
device_file = ""
wetterdaten = [
    ["Heute", "/", "/", "/", "/", "/"],
    ["Morgen", "/", "/", "/", "/", "/"],
    ["bermorgen", "/", "/","/","/", "/"]
]
optionen = {}
nachricht = "Es gibt keine neue Nachricht"
long = "??"
lat = "??"
notify = False
notify2 = False
max17048 = None
hoehe = "??"
shared_data = {"status56": "init2", "message": "","message2": "", "wetterdaten": wetterdaten, "funk":0,"timeout":0}
state = True
status = {
    'label1': 'Bereit',
    'label2': 'Bereit',
    'label3': 'Bereit'
}
myid = "7979173"
myname = "Pi2"
SENSOREN = []
ser = None
cords =""
server_id = ""
serial_number = "088713"
manager_check = 0
time_data = None
