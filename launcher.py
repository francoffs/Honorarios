import os
import subprocess
import sys
import time
import webbrowser
import threading
import socket

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def open_browser():
    while not is_port_in_use(8501):
        time.sleep(1)
    webbrowser.open("http://localhost:8501")

# Caminho para o script principal
script_path = resource_path('controle_financeiro.py')

# Iniciar o navegador em um thread separado
browser_thread = threading.Thread(target=open_browser)
browser_thread.start()

# Iniciar o Streamlit e esperar o processo terminar
subprocess.run([sys.executable, '-m', 'streamlit', 'run', script_path])
