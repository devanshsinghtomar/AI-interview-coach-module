import multiprocessing

bind = "0.0.0.0:8080"
workers = 2
worker_class = "sync"
timeout = 120
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# For better compatibility
reload = False
preload_app = False
