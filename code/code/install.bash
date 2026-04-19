#!/bin/bash
echo "Aktualisiere Paketliste..."
sudo apt update
echo "Installiere pip (falls nicht vorhanden)..."
sudo apt install -y python3-pip
echo "Installiere Python Libraries..."
pip3 install flask --break-system-packages
echo "Flask Installiert"
pip3 install pyserial --break-system-packages
echo "serial Installiert"
pip3 install adafruit-blinka smbus2 --break-system-packages
echo "blinka-smbus2 Installiert"
pip3 install adafruit-circuitpython-max1704x --break-system-packages
echo "MAX17048 Installiert"
pip3 install pytz --break-system-packages
echo "pytz Installiert"
pip3 install "mpmath==1.3.0" --break-system-packages
echo "mpmath Installiert"
pip3 install adafruit-circuitpython-bme280 --break-system-packages
echo "BME280 Installiert"
pip3 install ebyte-lora-e220-rpi --break-system-packages
echo "LORA Installiert"
sudo apt install ttyd
echo "ttyd Installiert"
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial 0  # UART aktivieren
sudo raspi-config nonint do_onewire 0
SERVICE_NAME=myapp
SCRIPT_PATH=/home/pi/code/app.py
echo "Erstelle systemd Service..."
sudo bash -c "cat > /etc/systemd/system/$SERVICE_NAME.service" <<EOF
[Unit]
Description=LoRa App
After=network.target

[Service]
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/python3 /home/pi/code/app.py
WorkingDirectory=/home/pi/code
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF
echo "Aktiviere Service..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "Starte Service..."
sudo systemctl start $SERVICE_NAME
echo "Fertig!"
