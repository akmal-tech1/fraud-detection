import json, urllib.request, subprocess, sys, time, os

os.chdir(r'C:\Users\akmal\OneDrive\Documents\Default Project\backend')
proc = subprocess.Popen(
    [r'venv\Scripts\python.exe', '-m', 'uvicorn', 'main:app', '--port', '8000', '--host', '127.0.0.1'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
time.sleep(3)

try:
    # Test list transactions
    req = urllib.request.Request('http://127.0.0.1:8000/api/transactions')
    response = urllib.request.urlopen(req, timeout=5)
    data = json.loads(response.read().decode())
    print('List transactions (first page):')
    print(json.dumps(data, indent=2)[:1000])
    print('...')

    # Test single transaction (use an existing ID from the DB)
    req2 = urllib.request.Request('http://127.0.0.1:8000/api/transactions/1')
    response2 = urllib.request.urlopen(req2, timeout=5)
    data2 = json.loads(response2.read().decode())
    print()
    print('Transaction 1:')
    print(json.dumps(data2, indent=2)[:1000])
    print('...')
except Exception as e:
    print(f'Error: {e}')

proc.terminate()
proc.wait()
print('Done')