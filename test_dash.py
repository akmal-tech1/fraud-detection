import json, urllib.request, sys, time, subprocess

# Start server
proc = subprocess.Popen(
    [r'backend\venv\Scripts\python.exe', '-m', 'uvicorn', 'main:app', '--port', '8000', '--host', '127.0.0.1'],
    cwd=r'C:\Users\akmal\OneDrive\Documents\Default Project\backend',
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

time.sleep(3)

try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/model/dashboard/summary')
    response = urllib.request.urlopen(req, timeout=5)
    data = json.loads(response.read().decode())
    print('Dashboard summary:')
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f'Error contacting API: {e}')

proc.terminate()
proc.wait()
print('Done')