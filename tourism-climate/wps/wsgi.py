from pywps import Service
from processes import processes

# Для PyWPS 4.7.0 конфиг передается через cfg или не передается
application = Service(processes=processes)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 5001, application, use_debugger=True, use_reloader=True)