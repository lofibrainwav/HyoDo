from datetime import datetime

import requests

stream_url = "http://127.0.0.1:3000/api/debugging/stream"

print(f"[{datetime.now()}] Connecting to {stream_url}")
r = requests.get(stream_url, stream=True)

# Post the event in another process/thread or just before?
# Let's use a timeout-based approach or just use curl for one side.
