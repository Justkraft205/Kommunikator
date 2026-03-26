# -*- coding: latin-1 -*-
import shared, time
from lora_e220 import LoRaE220, print_configuration
from lora_e220_operation_constant import ResponseStatusCode
from datetime import datetime

def empfange_nachricht(server_id, fixed, timeout=10):
    global var1, var2
    startzeit = datetime.now().timestamp()
    print(f"{startzeit}:Startzeit")
    try:
        while True:
            if shared.lora.available() > 0:
                code, message = shared.lora.receive_message()
                time.sleep(0.1)
                zeit = datetime.now().strftime("%H:%M:%S")
                print(f"[{zeit}] Nachricht empfangen: {message}")
                if message is None:
                    print("Keine Nachrich")
                    continue
                if fixed and ";" in message:
                        print("----- Empfangen -----")
                        result = message.split(";", 1)[1]
                        return result, "1"
                else:
                    if ":" in message:
                        var1, var2 = [teil.strip() for teil in message.split(":", 1)]
                        if var1 == server_id or server_id == 0:
                            return var2, var1
                    else: print("Ungültiges Nachrichtenformat.")
            if datetime.now().timestamp() - startzeit > timeout:
                print(f"Fehler Zeit:{datetime.now().timestamp()}")
                print("Kein Empfang.")
                return "404", "404"
    except KeyboardInterrupt:
        return None
