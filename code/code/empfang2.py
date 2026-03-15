# -*- coding: latin-1 -*-
import serial
from datetime import datetime
from lora_e220 import LoRaE220, print_configuration
from lora_e220_operation_constant import ResponseStatusCode
import shared, time

def empfang_normal(server_id, timeout=10):

    startzeit = time.time()

    while True:
        if shared.lora.available() > 0:
            print("available:", shared.lora.available())
            code, message = shared.lora.receive_message()
            print(ResponseStatusCode.get_description(code))

            if isinstance(message, bytes):
                try:
                    message = message.decode("utf-8")
                except:
                    print("Hex:", message.hex())
                    message = message.hex()

            print("RAW:", message)

            if ":" in message:

                var1, var2 = message.split(":", 1)
                var1 = var1.strip()
                var2 = var2.strip()
                print("ID:", var1)
                print("TEXT:", var2)
                if var1 == server_id or server_id == 0:
                    return var2, var1

            else:
                print("Ungültiges Nachrichtenformat")

        if time.time() - startzeit > timeout:
            print("Timeout ? kein Empfang")
            return "404", "404"
