# -*- coding: latin-1 -*-
import shared
from lora_e220 import LoRaE220
def senden(server_id, message):
    try:
        shared.lora.send_transparent_message(f"{server_id}:{message}\n".encode('utf-8'))
        print("Gesendet")
    except Exception as e:
        print("Fehler beim Senden:", e)
