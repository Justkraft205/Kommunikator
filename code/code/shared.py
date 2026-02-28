# Lora:-----------------------------------------------------------------------------------------------------------------
M1_PIN = 23
M0_PIN = 24
aux_pin = 25
lora = None
current_power = 13
current_freq = 18
battery_level = 0
#Sensoren:--------------------------------------------------------------------------------------------------------------
temp_f = 0
skalas = "°C,z,hpa,y,%,x"
temp_c = 0
bus = None
bme280 = None
logger_service = False
logger_data = False
last_file = None
celsius = True
SENSOREN = []
sensors = [
        ["BMP", 0x76],
        ["MAX17048", 0x36]
    ]
i2c = None
sensor_data = {}
wert = ""
kontakte = []
send = ""
device_file = ""
setWifiStrength = 2  # 0 bis 4
fehler = ""
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
ser = None
cords =""
server_id = ""
serial_number = "088713"
manager_check = 0
time_data = None
test = None
