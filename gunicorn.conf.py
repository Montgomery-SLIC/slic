import multiprocessing

# (2 × CPU cores) + 1 workers as per architectural decision
workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = 'gthread'
threads = 4
timeout = 120
keepalive = 5

# Staging: port 9294 / Production: port 9295
# Override with GUNICORN_BIND env var in systemd unit
bind = '127.0.0.1:9294'

accesslog = '/var/log/slic/access.log'
errorlog = '/var/log/slic/error.log'
loglevel = 'info'

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100
