"""gunicorn settings.

One worker on purpose: the live-save notifications (SSE), the per-player locks and the
rate limiter live in process memory. Concurrency comes from threads, and every open game
tab holds one thread for its SSE stream.
"""
bind = "0.0.0.0:8080"
workers = 1
worker_class = "gthread"
threads = 128
timeout = 120
graceful_timeout = 30
keepalive = 30
accesslog = "-"
errorlog = "-"
