from adafruit_bme280 import basic as adafruit_bme280
import shared, board, adafruit_max1704x, time, smbus2

def restarting_i2c(bus_id=1):
    try:
        shared.bus.close()
        time.sleep(0.1)
        shared.bus = smbus2.SMBus(bus_id)
        return True
    except Exception: return False

def read_sensors(sensoren):
    skala = shared.skalas.split(",")
    shared.sensor_data = {}
    ok, name = bme280(skala, sensoren)
    if not ok: print(f"Fehler bei: {name}")
    #Füge unter halb dieser Zeile deine eigenen Sensoren hinzu
    return True

def check_i2c_devices(sensor_list):
    sensoren = {}
    shared.i2c = board.I2C()
    print("Aktive Sensoren:", shared.SENSOREN)
    for name, address in sensor_list:
        try:
            shared.bus.read_byte(address)
            print(f"{name} antwortet auf Adresse {hex(address)}")
            if address == 0x36: sensoren["max17048"] = adafruit_max1704x.MAX17048(shared.i2c)
            if address == 0x76:
                sensor = adafruit_bme280.Adafruit_BME280_I2C(shared.i2c, address=0x76)
                sensor.mode = adafruit_bme280.MODE_NORMAL
                sensoren["BME280"] = sensor
            #Füge unter halb dieser Zeile deine eigenen Sensoren hinzu
        except OSError:
            print(f"{name} antwortet NICHT auf Adresse {hex(address)}")
            if address == 0x36: shared.battery_level = -10
    return sensoren

#Hier der Lese code deiner Sensoren-------------------------------------------------------------------------------------

def bme280(teile, sensoren):
    if "BME280" in sensoren:
        x = round(sensoren["BME280"].humidity, 1)
        y = round(sensoren["BME280"].pressure, 1)
        z = round(sensoren["BME280"].temperature, 1)
        shared.sensor_data.update({
            "Luftfeuchtigkeit": f"{eval(teile[5])} {teile[4]}",
            "Luftdruck": f"{eval(teile[3])} {teile[2]}",
            "Temperatur": f"{eval(teile[1])} {teile[0]}"})
        for s in ["Temperatur", "Luftdruck", "Luftfeuchtigkeit"]:
            if s not in shared.header:shared.header.append(s)
        return True, "BME280"
    else: return False, "BME280"

