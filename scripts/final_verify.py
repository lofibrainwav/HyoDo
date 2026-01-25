import threading
import time

import requests


def listen() -> None:
    print("Connecting...")
    try:
        # Use stream=True and iter_lines to be real-time
        r = requests.get("http://127.0.0.1:3000/api/debugging/stream", stream=True, timeout=10)
        for line in r.iter_lines():
            if line:
                decoded = line.decode()
                print(f"GOT: {decoded}")
                if "VERIFY_ME" in decoded:
                    print("✅ SENTINEL FOUND")
                    return
    except Exception as e:
        print(f"Listen error: {e}")


t = threading.Thread(target=listen)
t.start()
time.sleep(2)

print("Emitting...")
res = requests.post("http://127.0.0.1:8010/api/debugging/emit", json={"message": "VERIFY_ME"})
print(f"Emit status: {res.status_code}, {res.text}")

t.join(timeout=5)
if t.is_alive():
    print("❌ FAILED: Timeout reached")
else:
    print("✅ SUCCESS")
