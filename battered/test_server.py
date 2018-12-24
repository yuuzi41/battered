from battered import BatteredMiddleware
from wsgiref.simple_server import make_server, demo_app

battered = BatteredMiddleware(demo_app, {})

with make_server('', 8000, battered) as httpd:
    print("start port 8000 ...")
    httpd.serve_forever()

