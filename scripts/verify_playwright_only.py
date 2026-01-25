import json
import subprocess


def verify_playwright() -> None:
    cmd = [
        "python3",
        "packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py",
    ]
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    print("🔹 Testing Playwright Bridge (Dedicated)...")

    # Navigate
    nav_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "browser_navigate",
            "arguments": {"url": "http://example.com"},
        },
    }

    try:
        process.stdin.write(json.dumps(nav_req) + "\n")
        process.stdin.flush()

        response_line = process.stdout.readline()
        print(f"Navigate Response: {response_line.strip()}")
        resp = json.loads(response_line)
        content = json.loads(resp["result"]["content"][0]["text"])

        if content.get("success"):
            print("✅ Browser Navigation Success")
            print(f"   Title: {content.get('title')}")

            # Scrape
            scrape_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "browser_scrape",
                    "arguments": {"selector": "h1"},
                },
            }
            process.stdin.write(json.dumps(scrape_req) + "\n")
            process.stdin.flush()

            response_line = process.stdout.readline()
            print(f"Scrape Response: {response_line.strip()}")
            resp = json.loads(response_line)
            content = json.loads(resp["result"]["content"][0]["text"])

            if content.get("success") and "Example Domain" in content.get("content", ""):
                print("✅ Browser Scrape Success")
            else:
                print(f"❌ Scrape Failed: {content}")
        else:
            print(f"❌ Navigation Failed: {content.get('error')}")

    except Exception as e:
        print(f"❌ Test Error: {e}")
        stderr = process.stderr.read()
        print(f"STDERR: {stderr}")
    finally:
        process.terminate()


if __name__ == "__main__":
    verify_playwright()
