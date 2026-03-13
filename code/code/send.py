# -*- coding: latin-1 -*-
import shared
from lora_e220 import LoRaE220

def senden(server_id, message,mode=None, channel=None, id1=None, id2=None):
    try:
        if not "x" in server_id:
            shared.lora.send_transparent_message(f"{server_id}:{message}\n")  # nur str, kein .encode()
            print(f"Sende transparent: {server_id}:{message}")
            return True
        else:
            id1, id2 = server_id.split(":")
            id1 = int(id1, 16)
            id2 = int(id2, 16)
            shared.lora.send_fixed_message(id1, id2, channel, f"fix:{message}".encode('utf-8'))
            print(f"Sende fixed: fix:{message}")
            return True
    except Exception as e: return False
