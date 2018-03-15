import socket
from TNU.modules import _SEGMENT
from TNU.modules._STATES import _pTYPES

s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

with open('send.txt','r') as file:
    buffer = file.read()
#  send data in the buffer MSS is head+MAX
i = 0
seq = 0
MAX = 1000
while i < len(buffer):
    sub_buffer = buffer[i: min(i + MAX, len(buffer))]
    segmnt = _SEGMENT.SEGMENT(_pTYPES.CHUNK, seq, 0, 0, 0, sub_buffer)  # pkt_type, pkt_seq, pkt_ack, pkt_ratio, opt, pkt_data
    seq += 1
    packet = segmnt.encap()
    s.sendto(packet.encode(), ('127.0.0.1', 9889))
    i = min(i + MAX, len(buffer))

segmnt = _SEGMENT.SEGMENT(_pTYPES.END, seq, 0, 0, 0, '')  # pkt_type, pkt_seq, pkt_ack, pkt_ratio, opt, pkt_data
packet = segmnt.encap()
s.sendto(packet.encode(), ('127.0.0.1', 9889))
# i = 0
# while segmnt[i:i+MAX]:
#     s.sendto(segmnt[i:i+MAX].encode(), ('127.0.0.1', 9889))
#     i += MAX
s.close()