# Lora:-----------------------------------------------------------------------------------------------------------------
M1_PIN = 23
M0_PIN = 24
aux_pin = 25
lora = None
current_power = 13
current_freq = 18
ADDH = None
ADDL = None
#Sensoren:--------------------------------------------------------------------------------------------------------------
skalas = "°C,z,hpa,y,%,x"
bus = None
logger_service = False
header = []
logger_data = None
logger_data2 = False
last_file = None
SENSOREN = []
sensors = [
        ["BMP", 0x76],
        ["MAX17048", 0x36]
    ]
i2c = None
sensor_data = {}
battery_level = 0
wert = ""
kontakte = []
send = ""
device_file = ""
setWifiStrength = 2  # 0 bis 4
fehler = ""
fehler2 = ""
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
hoehe = "??"
state = True
myid = "7979173"
myname = "Pi2"
fixed_message = False
ser = None
cords =""
server_id = ""
serial_number = "088713"
manager_check = 0
time_data = None
test = None
thread_wait = False
file_name = None

# I guess can weg
temp_c = 0
temp_f = 0
shared_data = {"status56": "init2", "message": "","message2": "", "wetterdaten": wetterdaten, "funk":0,"timeout":0}
status = {
    'label1': 'Bereit',
    'label2': 'Bereit',
    'label3': 'Bereit'
}
celsius = True
