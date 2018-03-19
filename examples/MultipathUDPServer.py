import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES
from queue import PriorityQueue
from threading import Thread, Event
import time


class slave_config:
    addr = '127.0.0.1'
    port = 9881
    path_list = []
    slave_tuple = (addr, port)


class local(tuple):
    address = ('127.0.0.1', 9880)


class Master_TCP(socket.socket):
    def __init__(self):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.s != -1
        self.buffer = []
        self.slaves = {}  # PathID:Slave_UDP
        self.master: socket = None

    def wait_for_handshake(self):
        self.s.bind(local.address)
        self.s.listen(1)
        self.master, client_addr = self.s.accept()
        print("debug: Accepted connection from {0} ...".format(client_addr))

    def request_to_add_slave(self):
        segment = SEGMENT(_pTYPES.REQUEST_TO_ADD_SLAVE, 0, 0, 1, 0, 0,
                          str(local.address))  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
        send_packet = segment.encap()  # 打包并发出
        self.master.send(send_packet.encode())
        print('debug: Sending request to add a slave...')
        recv_packet = self.master.recv(65535)  # 得到数据包
        recv_segment = SEGMENT.decap(recv_packet.decode())
        if recv_segment.pkt_type == _pTYPES.RESPONSE_TO_ADD_SLAVE:
            slave_tuple = (recv_segment.pkt_data.split(',')[0], int(recv_segment.pkt_data.split(',')[1]))
            print('debug: Now slave {0} has been added...'.format(slave_tuple))
            m.slaves[segment.pathid] = slave_tuple

    def slave_run(self, pathid: int):
        t = Thread(target=self.slaves[pathid].grabdata, args=self.buffer)
        t.start()
        # threading


m = Master_TCP()
m.wait_for_handshake()
m.request_to_add_slave()
print(m.slaves)
