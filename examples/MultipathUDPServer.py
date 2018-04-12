# -*- coding: utf-8 -*-
import socket
from queue import Queue
from TNU.modules.xSEGMENT import SEGMENT
from TNU.modules.xSTATES import pTYPES
from TNU.modules.xBUFFER import BUFFER
from threading import Thread, Event
import time


class count_pkt:
    count = 0


class slave_config:
    def __init__(self, addr, port, sock):
        self.addr = addr
        self.port = 9880
        self.sock = sock
        self.ready_to_send = []
        self.slave_tuple = (addr, port)


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


class Master_TCP(socket.socket):
    def __init__(self):
        super().__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.s != -1
        self.buffer_to_send = BUFFER()  # 里面是打包好的包，SEGMENT类型，便于后面加pathid和seq，这个buffer是要发送的
        self.buffer = BUFFER()  # 这个buffer存放了所有的包，用于重传
        self.slaves = {}  # PathID:slave_config
        self.slave_start_event = {}
        self.slave_close_event = {}
        self.retrans_seq = []
        self.slave_offset = 1
        self.master = None

    def wait_for_handshake(self):
        self.s.bind(server_address.addr_dict[0])
        self.s.listen(1)
        self.master, client_addr = self.s.accept()
        print("debug: Accepted connection from {0} ...".format(client_addr))

    def request_to_add_slave(self):
        segment = SEGMENT(pTYPES.REQUEST_TO_ADD_SLAVE, 0, 0, self.slave_offset, 0, 0,
                          str(server_address.addr_dict[0]))
        # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
        send_packet = segment.encap()  # 打包并发出
        self.master.send(send_packet.encode())
        print('debug: Sending request to add a slave...')
        recv_packet = self.master.recv(65535)  # 得到数据包
        print('debug: response received...')
        recv_segment = SEGMENT.decap(recv_packet.decode())
        if recv_segment.pkt_type == pTYPES.RESPONSE_TO_ADD_SLAVE:
            slave_tuple = (  # 从client获得client的本地地址
                recv_segment.pkt_data.split(',')[0].strip('\'').strip('\''), int(recv_segment.pkt_data.split(',')[1]))
            # IP,port,socket
            print('debug: Now slave {0} has been added...'.format(slave_tuple))
            self.slaves[segment.pathid] = slave_config(slave_tuple[0], slave_tuple[1],
                                                       socket.socket(socket.AF_INET, socket.SOCK_DGRAM))
            this_slave = self.slaves[segment.pathid]
            this_slave.sock.bind(server_address.addr_dict[segment.pathid])
            self.slave_start_event[segment.pathid] = Event()  # 等待slave开始运行后再进行操作
            self.slave_offset += 1

    def kill_master(self):
        segment = SEGMENT(pTYPES.KILL_MASTER, 0, 0, 0, 0, 0,
                          '')  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
        send_packet = segment.encap()  # 打包并发出
        self.master.send(send_packet.encode())
        print('debug: Slaves\' revolution!!!')
        recv_packet = self.master.recv(65535)  # 得到数据包
        recv_segment = SEGMENT.decap(recv_packet.decode())
        if recv_segment.pkt_type == pTYPES.KILL_MASTER:
            print('debug: Long live the Soviet!!!')
            sock = self.master
            sock.close()

    def send_data_through_slave(self, pathid, ready_to_send):
        if self.slaves.__contains__(pathid):
            this_slave = self.slaves[pathid]
            self.slave_start_event[pathid].wait()  # 等待slave开始运行后再进行操作
            while ready_to_send:  # how to stop
                send_data = this_slave.ready_to_send.pop(0)
                time.sleep(0.05)
                this_slave.sock.sendto(send_data.encode(), this_slave.slave_tuple)
                print(
                    'debug: slave {0} sends a packet {1} -> {2}...'.format(pathid, this_slave.sock.getsockname(),
                                                                           this_slave.slave_tuple))

    def feed_slave(self):
        count = 0
        while not self.buffer_to_send.empty():
            for pathid, slave_conf in self.slaves.items():
                if self.slave_start_event[pathid].isSet():  # 该子流是否已打开
                    this_slave = self.slaves[pathid]
                    # 是否还有没有feed的数据？
                    if not self.buffer_to_send.empty():
                        this_seq, raw_segment = self.buffer_to_send.get()
                    if self.buffer_to_send.qsize() < self.slaves.__len__():  # buffer大小小于slaves队列长度
                        raw_segment.pkt_type = pTYPES.END_OF_SLAVE
                    raw_segment.pathid = pathid
                    this_slave.ready_to_send.append(raw_segment.encap())
                    count += 1
        count_pkt.count = count

    def waiting_for_ack(self):
        while True:
            print('debug: Server is waiting for acks...')
            ack_pkt = self.master.recv(65535).decode()
            ack_segment = SEGMENT.decap(ack_pkt)
            if ack_segment.pkt_type == pTYPES.ACK:  # 这里要给一个mailbox发送pkt_seq，然后重传这些包
                self.retrans_seq.append(ack_segment.pkt_ack)
                print('debug: Got a ACK{}'.format(ack_segment.pkt_ack))
            else:
                if ack_segment.pkt_type == pTYPES.DONE_TRANSMISSION:
                    print('debug: Client done...')
                    break

    # def slave_run(self, pathid: int):  # meixiehao!!
    #     t = Thread(target=self.slaves[pathid].send_data_through_slave, args=self.buffer)
    #     t.start()
    #     self.slave_start_event[pathid].set()  # 指示该slave已经开始运行
    #     # threading


m = Master_TCP()
m.wait_for_handshake()
m.request_to_add_slave()
print(m.slaves)
m.request_to_add_slave()
print(m.slaves)
segment = SEGMENT(pTYPES.NO_MORE_SLAVE, 0, 0, 0, 1, 0, '')
m.master.send(segment.encap().encode())

pkt = m.master.recv(65535).decode()
segment = SEGMENT.decap(pkt)
if segment.pkt_type == pTYPES.I_WANT_DATA:
    pass
else:
    print('debug: NO Data wanted..')

with open('send.txt', 'r') as file:
    raw_file = str(file.read())
seq = 0
for i in range(0, len(raw_file), 5000):
    if i + 5000 < len(raw_file):
        this_segment = SEGMENT(pTYPES.CHUNK, seq, 0, 0, 1, 0, raw_file[i: i + 5000])
        m.buffer_to_send.put((this_segment.pkt_seq, this_segment))
        m.buffer.put((this_segment.pkt_seq, this_segment))
    else:
        this_segment = SEGMENT(pTYPES.END, seq, 0, 0, 1, 0, raw_file[i: i + 5000])
        m.buffer_to_send.put((this_segment.pkt_seq, this_segment))
        m.buffer.put((this_segment.pkt_seq, this_segment))
    # m.buffer.put_segment_and_encap(SEGMENT(_pTYPES.CHUNK, seq, 0, 0, 1, 0, raw_file[i: i + 60000]))  # 没有封装成str
    seq += 1

m.slave_start_event[1].set()
m.slave_start_event[2].set()
m.feed_slave()
pathids = list(m.slaves.keys())
slave_post_office = []
start = time.time()
for pathid in pathids:
    salve_buffer = m.slaves[pathid].ready_to_send
    t_send_through_slave = Thread(target=m.send_data_through_slave, args=(pathid, salve_buffer))
    slave_post_office.append(t_send_through_slave)

# 增加一个线程 用于接收ack
# 再增加一个线程 用于向ready to send里面增加包

for slave in slave_post_office:
    slave.start()
for slave in slave_post_office:
    slave.join()

print('debug: {0} packets in total!!!\ntime:{1}s...'.format(count_pkt.count, time.time() - start))
# m.kill_master()

# while i < len(raw_buffer):
#     sub_buffer = raw_buffer[i: min(i + 60000, len(raw_buffer))]
#     segment = SEGMENT(_pTYPES.CHUNK, seq, 0, ) # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
#     i = min(i + 60000, len(raw_buffer))
