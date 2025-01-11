import os

workers = 1  # WebSocket works better with a single worker
worker_class = 'eventlet'
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
keepalive = 120
worker_connections = 1000
timeout = 300
graceful_timeout = 300
