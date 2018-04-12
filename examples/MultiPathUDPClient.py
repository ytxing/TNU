# -*- coding: utf-8 -*-
import socket
from TNU.modules.xBUFFER import BUFFER
from TNU.modules.xSEGMENT import SEGMENT
from TNU.modules.xSTATES import pTYPES
from threading import Thread, Event
import time


class local_information:
    addr = '10.0.0.2'
    port = 9881
    pathid_list = []
    slave_tuple = (addr, port)


class server_address:
    addr_dict = {
        0: ('10.0.0.1', 9881),
        1: ('10.0.0.1', 9883),
        2: ('10.0.0.1', 9885)
    }


class client_address:
    addr_dict = {
        0: ('10.0.0.1', 9882),
        1: ('10.0.0.1', 9884),
        2: ('10.0.0.1', 9886)
    }


class slave_config:
    def __init__(self, addr: str, port: int, sock: socket.socket):
        self.addr = addr
        self.port = port
        self.sock = sock
        self.ready_to_send = []
        self.slave_tuple = (addr, port)


class Master_TCP(socket.socket):
    def __init__(self):
        super().__init__()
        self.master = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.master != -1
        self.buffer = BUFFER()
        self.slaves = {}  # PathID:Slave_config
        self.slave_offset = 1
        self.slave_start_event = {}

    def handshake(self, server_tuple: tuple):
        self.master.bind(client_address.addr_dict[0])
        self.master.connect(server_tuple)
        print("debug: Connecting to {0} ...".format(server_tuple))

    def add_slave(self, pathid, _slave_tuple: (str, int)):
        """

        :param int:
        :param _slave_tuple: tuple
        :type pathid: int
        """
        # after Server requests to add a slave, master decided that should be _slave_tuple
        assert isinstance(pathid, int)
        if not self.slaves.__contains__(pathid):
            self.slaves[pathid] = slave_config(_slave_tuple[0], _slave_tuple[1],
                                               socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
            this_slave = self.slaves[pathid]
            this_slave.sock.bind(client_address.addr_dict[pathid])  # binding on slave tuple
            print('debug: PathID {0} is {1!s} ...'.format(pathid, _slave_tuple))
            segment = SEGMENT(pTYPES.RESPONSE_TO_ADD_SLAVE, 0, 0, pathid, 0, 0,
                              str(client_address.addr_dict[pathid]).strip('(').strip(')'))
            # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
            self.master.send(segment.encap().encode())
        else:
            print('debug: {0} has already existed...'.format(pathid))

    def slave_run(self, pathid: int):
        t = Thread(target=self.slaves[pathid].grabdata, args=self.buffer)
        t.start()
        # threading

    def show_buff(self):
        print(self.buffer)

    def grabdata(self, pathid: int, buffer: BUFFER):
        assert isinstance(buffer, BUFFER)
        if self.slaves.__contains__(pathid):
            this_slave = self.slaves[pathid]
            while True:
                print('debug: waiting for packet at Path{0}...'.format(this_slave.sock.getsockname()))
                data, source = this_slave.sock.recvfrom(65535)
                print('debug: got a packet at Path{0}...'.format(pathid))
                this_segment = SEGMENT.decap(
                    data.decode())  # decap the data, the data is encoded and need to be decoded
                this_segment.showseg('')
                buffer.put((this_segment.pkt_seq, this_segment.encap()))
                # buffer.put_segment_and_encap(this_segment)
                if this_segment.pkt_type == pTYPES.END or this_segment.pkt_type == pTYPES.END_OF_SLAVE:
                    break

    def waiting_for_order(self):
        while True:
            print('debug: Master is waiting for order...')
            recv_packet = self.master.recv(65535).decode()
            print(recv_packet)
            if recv_packet == '':
                print('debug: empty packet wtf...?')
                break
            segment = SEGMENT.decap(recv_packet)
            if segment.pkt_type == pTYPES.REQUEST_TO_ADD_SLAVE:
                print('debug: sending message to add slave...\ncreat a event of path{}'.format(segment.pathid))
                # self.slave_start_event[segment.pathid] = Event()
                self.add_slave(segment.pathid, server_address.addr_dict[segment.pathid])
                self.slave_offset += 1
            else:
                if segment.pkt_type == pTYPES.KILL_MASTER:
                    segment = SEGMENT(pTYPES.KILL_MASTER, 0, 0, 0, 0, 0,
                                      '')  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
                    send_packet = segment.encap()  # 打包并发出
                    self.master.send(send_packet.encode())
                    print('debug: Long live the Soviet!!!')
                    break
                else:
                    if segment.pkt_type == pTYPES.MASTER_HEARTBEAT:
                        print('Master is  alive!')
                    else:
                        if segment.pkt_type == pTYPES.NO_MORE_SLAVE:
                            break


        print('debug: No longer waiting, Master is dead...')


m = Master_TCP()
m.handshake(server_address.addr_dict[0])  # Server ip
t_master = Thread(target=m.waiting_for_order, daemon=True)
t_master.start()
t_master.join()

segment = SEGMENT(pTYPES.I_WANT_DATA, 0, 0, 0, 1, 0, '')
m.master.send(segment.encap().encode())
print('debug: I want data...')

data_segment = []
pathids = list(m.slaves.keys())
slave_post_office = []
for pathid in pathids:
    t_slave_grab_data = Thread(target=m.grabdata, args=(pathid, m.buffer))
    slave_post_office.append(t_slave_grab_data)
for slave in slave_post_office:
    slave.start()
time.sleep(3)
for slave in slave_post_office:
    slave.join()
# m.grabdata(1, m.buffer)
seq = 0

while not m.buffer.empty():
    this_seq, this_segment = m.buffer.get()
    if seq != this_seq:
        print('should be {0} but {1}'.format(seq, this_seq))
    seq += 1
    data_segment.append(SEGMENT.decap(this_segment).pkt_data)
print('debug: {}packets in total!!!'.format(seq))

data = str.join('', data_segment)
with open('recv.txt', 'w') as file:
    file.write(data)

print('done!')
# m.slave_run(0)
<<<<<<< HEAD
=======

>>>>>>> linux_version0.1
# assert master != -1
# master.connect(('127.0.0.1', 9880))
# master.send('GET /data.txt')
# data = master.recv(65535)  # data='127.0.0.1:9881'
# slave_tuple = (data.split(':')[0], data.split(':')[1])  # data will be sent here
# # 使用线程接收数据，并且实现端口支持从master获取控制信息。数据
# # master循环接收来自服务器端的反馈
# buffer = PriorityQueue()
