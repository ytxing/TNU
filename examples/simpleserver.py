import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
buff = []
#i = 0
s.bind(('127.0.0.1', 9889))
print('Binding UDP on 9889...')
while True:
    data, addr = s.recvfrom(65535)
    segmnt = SEGMENT.decap(data.decode())  # decap the data, the data is encoded and need to be decoded
    segmnt.showseg('all')
    print('Receiving from {0!r}{1}...'.format(addr, segmnt.pkt_seq))
    #i += 1
    if segmnt.pkt_type == _pTYPES.END:
        break
    else:
        if segmnt.pkt_type == _pTYPES.CHUNK:
            buff.append(segmnt.pkt_data)
print('break')
buffer = "".join(buff)
s.close()



with open('recv.txt', 'w') as file:
    file.write(buffer)



