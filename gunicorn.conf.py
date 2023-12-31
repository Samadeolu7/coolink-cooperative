# gunicorn.conf.py

import multiprocessing

bind = "127.0.0.1:8080"
workers = multiprocessing.cpu_count() * 2 + 1
errorlog = "error.log"
accesslog = "access.log"
pidfile = "gunicorn.pid"
loglevel = "info"
