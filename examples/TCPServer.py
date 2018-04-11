import socket
import time
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('10.0.0.1', 9880))
s.listen(1)
sock, client = s.accept()

with open('send.txt', 'r') as file:
    buff = str(file.read())

start = time.time()
sock.send(buff.encode())
print('time:{}'.format(time.time() - start))
