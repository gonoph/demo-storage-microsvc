import os

workers = int(os.getenv('GUNICORN_PROCESSES', '3'))
threads = int(os.getenv('GUNICORN_THREADS', '1'))
loglevel = os.getenv('LOGLEVEL', 'warning').lower()

forwarded_allow_ips = '*'
secure_scheme_headers = { 'X-Forwarded-Proto': 'https' }

logconfig = os.getenv('LOGCONFIG', '/opt/app-root/src/logging.conf')
