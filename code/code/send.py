# -*- coding: latin-1 -*-
import shared
from lora_e220 import LoRaE220

def senden(server_id, message, channel):
    try:
        print("senden aktiviert")
        print(server_id)
        if not ":" in server_id:
            shared.lora.send_transparent_message(f"{server_id}:{message}\n")  # nur str, kein .encode()
            print(f"Sende transparent: {server_id}:{message}")
            return True
        else:
            id1, id2 = server_id.split(":")
            shared.lora.send_fixed_message(int(id1), int(id2), channel, message)
            print(f"Sende fixed:{message}")
            return True
    except Exception as e:
        print(e)
        print("Fehler beim senden in send.py")
        return False
