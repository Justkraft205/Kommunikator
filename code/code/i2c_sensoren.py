from adafruit_bme280 import basic as adafruit_bme280
import shared, board, adafruit_max1704x, time, smbus2

def restarting_i2c(bus_id=1):
    try:
        shared.bus.close()
        shared.SENSOREN = []
        time.sleep(0.5)
        shared.bus = smbus2.SMBus(bus_id)
        return True
    except Exception as e: return False


def check_i2c_devices(sensor_list):
    shared.i2c = board.I2C()
    print("Aktive Sensoren:", shared.SENSOREN)
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
            print("Es wird gemacht")
        except OSError:
            print(f"{name} antwortet NICHT auf Adresse {hex(address)}")
            if address == 0x36: shared.battery_level = -10

def read_sensors():
    teile = shared.skalas.split(",")
    shared.sensor_data = {}
    print("Hier kannst du eigene Hinzufügen")
    ok, name = bme280(teile)
    if not ok: print(f"Fehler bei: {name}")
#-----------------------------------------------------------------------------------------------------------------------


def bme280(teile):
    if "BME280" in shared.SENSOREN:
        x = round(shared.bme280.humidity, 1)
        y = round(shared.bme280.pressure, 1)
        z = round(shared.bme280.temperature, 1)
        shared.sensor_data.update({
            "Luftfeuchtigkeit": f"{eval(teile[5])} {teile[4]}",
            "Luftdruck": f"{eval(teile[3])} {teile[2]}",
            "Temperatur": f"{eval(teile[1])} {teile[0]}"})
        for s in ["Temperatur", "Luftdruck", "Luftfeuchtigkeit"]:
            if s not in shared.header:shared.header.append(s)
        return True, "BME280"
    else: return False, "BME280"

