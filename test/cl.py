import socket
import time


# Verbindung zum lokalen Socket auf Port 5000 herstellen


# Daten senden

def com_thread(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_socket.connect(('localhost', 64321))
    client_socket.sendall(data.encode())
    response = client_socket.recv(1024).decode()
    client_socket.close()
    return response

while True:
    print(com_thread(input('>>')))
    time.sleep(5)
# Verbindung schließen



