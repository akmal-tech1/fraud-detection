import sys
sys.path.insert(0, r'C:\Users\akmal\OneDrive\Documents\Default Project\backend')
from main import app
routes = [(r.path, r.name) for r in app.routes if hasattr(r, 'path')]
for p, n in sorted(routes):
    print(f'{p:40s}  {n}')