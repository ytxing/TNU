import socket
from TNU.modules.xSEGMENT import SEGMENT
from TNU.modules.xSTATES import pTYPES

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
buff = []
# i = 0
s.bind(('127.0.0.1', 9889))
print('Binding UDP on 9889...')
while True:
    data, source = s.recvfrom(65535)
    segmnt = SEGMENT.decap(data.decode())  # decap the data, the data is encoded and need to be decoded
    segmnt.showseg('all')

    print('Receiving from {0!r}{1}...'.format(source, segmnt.pkt_seq))
    # segmnt = SEGMENT(_pTYPES.END, 0, segmnt.pkt_ack, 0, 0, '')  # pkt_type, pkt_seq, pkt_ack, pkt_ratio, opt, pkt_data
    # packet = segmnt.encap()
    # s.sendto(packet.encode(), source)

    # i += 1
    if segmnt.pkt_type == pTYPES.END:
        buff.append(segmnt.pkt_data)
        break
    else:
        if segmnt.pkt_type == pTYPES.CHUNK:  # ???
            buff.append(segmnt.pkt_data)
print('break')
buffer = "".join(buff)
s.close()

with open('recv.txt', 'w') as file:
    file.write(buffer)
