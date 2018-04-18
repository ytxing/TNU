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
        self.buffer_to_app = []
        self.data = []
        self.slaves = {}  # PathID:Slave_config
        self.slave_offset = 1
        self.slave_start_event = {}
        self.slave_close_event = Event()
        self.max_sequence = -1

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
                #

                buffer.put((this_segment.pkt_seq, this_segment.encap()))
                # buffer.put_segment_and_encap(this_segment)
                if self.slave_close_event.isSet():
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

    def aggregate_buffer(self, ratio: float, total_seq: int):
        start = time.time()
        t_timer = Thread(target=self.timer)
        t_timer.start()
        while self.max_sequence / self.buffer.total_sequence < ratio:
            time.sleep(0.02)
            if not self.buffer.empty():
                this_seq, this_packet = self.buffer.get()
                this_segment = SEGMENT.decap(this_packet)
                print('debug: {}/{}'.format(self.max_sequence, this_segment.pkt_seq))
                if self.max_sequence + 1 == this_segment.pkt_seq:  # 正常，没有失序包
                    self.buffer_to_app.append(this_segment.pkt_data)
                    self.max_sequence = this_segment.pkt_seq
                    ack_segment = SEGMENT(pTYPES.ACK, 0, self.max_sequence, this_segment.pathid,
                                          this_segment.pkt_ratio, this_segment.opt, '')  # ACK目前最大的包
                    ack_packet = ack_segment.encap()
                    self.master.send(ack_packet.encode())
                    print('debug: ACK{}'.format(self.max_sequence))
                else:
                    if self.max_sequence + 1 > this_segment.pkt_seq:  # 不正常，重复传输，丢掉
                        pass
                    else:  # 不正常，出现失序包，发送ack，等待重传，拿出来的放回去
                        self.buffer.put((this_seq, this_packet))
                        ack_segment = SEGMENT(pTYPES.OUT_OF_ORDER_PACKET, 0, self.max_sequence, this_segment.pathid,
                                              this_segment.pkt_ratio, this_segment.opt, '')  # ACK目前最大的包
                        ack_packet = ack_segment.encap()
                        self.master.send(ack_packet.encode())
                        print('debug: ACK{} out of order...'.format(self.max_sequence))
                        time.sleep(0.5)
        print('debug: enough packets, {}/{}={}'.format(self.max_sequence, self.buffer.total_sequence, ratio))
        self.slave_close_event.set()
        done_segment = SEGMENT(pTYPES.DONE_TRANSMISSION, 0, 0, 0, 1, 0, '')
        done_packet = done_segment.encap()
        self.master.send(done_packet.encode())
        self.data = str.join('', self.buffer_to_app)
        with open('recv.txt', 'w') as file:
            file.write(self.data)
        print('debug: file written...time{}'.format(time.time() - start))

    def timer(self):
        while not self.slave_close_event.isSet():
            time.sleep(0.8)
            if not self.buffer.empty():
                this_seq, this_packet = self.buffer.get()
                this_segment = SEGMENT.decap(this_packet)
                self.buffer.put((this_seq, this_packet))
                ack_segment = SEGMENT(pTYPES.OUT_OF_ORDER_PACKET, 0, self.max_sequence, this_segment.pathid,
                                      this_segment.pkt_ratio, this_segment.opt, '')  # ACK目前最大的包
                ack_packet = ack_segment.encap()
                self.master.send(ack_packet.encode())
                print('debug: ACK{} timer ACK...'.format(self.max_sequence))


m = Master_TCP()
m.handshake(server_address.addr_dict[0])  # Server ip
t_master = Thread(target=m.waiting_for_order, daemon=True)
t_master.start()
t_master.join()

segment = SEGMENT(pTYPES.I_WANT_DATA, 0, 0, 0, 1, 0, 'send.txt')
m.master.send(segment.encap().encode())
print('debug: I want data...')
packet = m.master.recv(65535).decode()
segment = SEGMENT.decap(packet)
if segment.pkt_type == pTYPES.CHUNK_INFO:
    m.buffer.total_sequence = segment.pkt_seq
    m.buffer.ratio = segment.pkt_ratio
    print('debug: Chunk information:\nmax_sequence{},ratio{}...'.format(segment.pkt_seq, segment.pkt_ratio))
else:
    print('debug: No chunk information...')



data_segment = []
pathids = list(m.slaves.keys())
slave_post_office = []
for pathid in pathids:
    t_slave_grab_data = Thread(target=m.grabdata, args=(pathid, m.buffer))
    slave_post_office.append(t_slave_grab_data)

t_aggregate_buffer = Thread(target=m.aggregate_buffer, args=(1, 120))
print('debug aggregating buffer...')
t_aggregate_buffer.start()
for slave in slave_post_office:
    slave.start()
time.sleep(3)
for slave in slave_post_office:
    slave.join()
t_aggregate_buffer.join()
# m.grabdata(1, m.buffer)
seq = 0
m.master.close()
# while not m.buffer.empty():
#     this_seq, this_segment = m.buffer.get()
#     if seq != this_seq:
#         print('should be {0} but {1}'.format(seq, this_seq))
#     seq += 1
#     data_segment.append(SEGMENT.decap(this_segment).pkt_data)
# print('debug: {}packets in total!!!'.format(seq))


print('done!')
