import os

workers = int(os.environ.get('GUNICORN_WORKERS', 4))
worker_class = 'eventlet'
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
keepalive = 120
