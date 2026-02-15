import requests
import time
import socket
import os

print("🔍 Starting Ollama Connectivity Diagnosis...")

urls_to_test = [
    "http://localhost:11434/api/tags",
    "http://127.0.0.1:11434/api/tags",
    "http://[::1]:11434/api/tags",
]


def check_socket(host, port):
    print(f"  checking socket {host}:{port}...", end="")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(" OPEN ✅")
            return True
        else:
            print(f" CLOSED/BLOCKED ({result}) ❌")
            return False
    except Exception as e:
        print(f" ERROR: {e}")
        return False
    finally:
        sock.close()


# 1. Check TCP Port
print("\n1. Testing TCP Connection:")
check_socket("127.0.0.1", 11434)
check_socket("localhost", 11434)

# 2. Check HTTP API
print("\n2. Testing HTTP API (requests):")
for url in urls_to_test:
    print(f"  Testing {url}...", end="")
    try:
        start = time.time()
        resp = requests.get(url, timeout=5)
        elapsed = time.time() - start
        if resp.status_code == 200:
            print(f" SUCCESS ✅ ({elapsed:.3f}s)")
            print(
                f"     Models: {[m['name'] for m in resp.json().get('models', [])[:3]]}..."
            )
        else:
            print(f" FAILED ❌ (Status: {resp.status_code})")
    except Exception as e:
        print(f" ERROR ❌: {type(e).__name__} - {e}")

print("\nDiagnosis Complete.")
