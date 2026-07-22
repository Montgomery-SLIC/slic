import multiprocessing

workers = (multiprocessing.cpu_count() * 2) + 1
worker_class = 'gthread'
threads = 4
timeout = 120
keepalive = 5

bind = '127.0.0.1:9295'

accesslog = '/var/log/slic/access_prod.log'
errorlog = '/var/log/slic/error_prod.log'
loglevel = 'warning'

max_requests = 1000
max_requests_jitter = 100
