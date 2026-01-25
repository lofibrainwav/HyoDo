import threading
import time

import requests


def listen() -> None:
    print("Connecting to Dashboard SSE Proxy...")
    try:
        # Use a timeout so it doesn't hang forever
        response = requests.get(
            "http://127.0.0.1:3000/api/debugging/stream", stream=True, timeout=10
        )
        print(f"Connected. Status: {response.status_code}")
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                print(f"Received: {decoded_line}")
                if "DIRECT_VERIFICATION_SENTINEL" in decoded_line:
                    print("✅ SENTINEL RECEIVED!")
                    return
    except Exception as e:
        print(f"Error: {e}")


# Start listener in a thread
t = threading.Thread(target=listen)
t.start()

# Wait for connection to stabilize
time.sleep(3)

# Emit sentinel
print("Emitting sentinel from Soul Engine...")
payload = {
    "source": "VERIFIER",
    "type": "sentinel",
    "message": "DIRECT_VERIFICATION_SENTINEL",
    "timestamp": "now",
}
requests.post("http://127.0.0.1:8010/api/debugging/emit", json=payload)

t.join(timeout=5)
if t.is_alive():
    print("❌ Verification timed out.")
else:
    print("✅ Verification successful.")
