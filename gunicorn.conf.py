import multiprocessing
import os

# (2 × CPU cores) + 1 workers as per architectural decision
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = 'gthread'
threads = 4
timeout = 120
keepalive = 5

# Staging: 127.0.0.1:9294 / Production: 127.0.0.1:9295
# Set GUNICORN_BIND in .env to override
bind = os.environ.get('GUNICORN_BIND', '127.0.0.1:9294')

accesslog = '/var/log/slic/access.log'
errorlog = '/var/log/slic/error.log'
loglevel = 'info'

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100
