import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES
from TNU.modules._BUFFER import BUFFER
from threading import Thread, Event
import time


class slave_config:
    def __init__(self, addr: str, port: int, sock: socket.socket):
        self.addr = addr
        self.port = 9881
        self.sock = sock
        self.ready_to_send = []
        self.slave_tuple = (addr, port)


class local(tuple):
    address = ('127.0.0.1', 9880)


class Master_TCP(socket.socket):
    def __init__(self):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.s != -1
        self.buffer = BUFFER()  # 里面是打包好的包，str类型
        self.slaves = {}  # PathID:slave_config
        self.slave_start_event = {}
        self.slave_close_event = {}
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
            slave_tuple = (
                recv_segment.pkt_data.split(',')[0], int(recv_segment.pkt_data.split(',')[1]))  # IP,port,socket
            print('debug: Now slave {0} has been added...'.format(slave_tuple))
            self.slaves[segment.pathid] = slave_config(slave_tuple[0], slave_tuple[1],
                                                       socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
            self.slave_start_event[segment.pathid] = Event()  # 等待slave开始运行后再进行操作

    def send_data_through_slave(self, pathid: int, buffer: BUFFER):
        if self.slaves.__contains__(pathid):
            this_slave: slave_config = self.slaves[pathid]
            self.slave_start_event[pathid].wait()  # 等待slave开始运行后再进行操作
            while not buffer.show_first_segment()[1] == 'RELEASE_SLAVE':  # how to stop
                this_slave.sock.sendto(buffer.get(), this_slave.slave_tuple)

    def slave_run(self, pathid: int):  # meixiehao!!
        t = Thread(target=self.slaves[pathid].send_data_through_slave, args=self.buffer)
        t.start()
        self.slave_start_event[pathid].set()  # 指示该slave已经开始运行
        # threading

    def feed_slave(self):
        for pathid, slave_conf in self.slaves.items():
            if self.slave_start_event[pathid].isSet():  # 该子流是否已打开
                this_slave: slave_config = self.slaves[pathid]
                if not self.buffer.empty():  # 是否还有没有feed的数据？
                    this_slave.ready_to_send.append(self.buffer.get())
                else:
                    break


m = Master_TCP()
m.wait_for_handshake()
m.request_to_add_slave()
print(m.slaves)
