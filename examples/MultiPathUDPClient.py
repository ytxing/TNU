import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES
from TNU.modules._BUFFER import BUFFER
from threading import Thread, Event
import time


class local_information:
    addr = '127.0.0.1'
    port = 9881
    pathid_list = []
    slave_tuple = (addr, port)


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

    def handshake(self, server_tuple: tuple):
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
            this_slave: slave_config = self.slaves[pathid]
            this_slave.sock.bind(_slave_tuple)
            print('debug: PathID {0} is {1!s} ...'.format(pathid, _slave_tuple))
            segment = SEGMENT(_pTYPES.RESPONSE_TO_ADD_SLAVE, 0, 0, pathid, 0, 0,
                              '{0},{1}'.format(this_slave.addr, str(
                                  this_slave.port)))  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
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
            this_slave: slave_config = self.slaves[pathid]
            while True:
                print('debug: waiting for packet at Path{0}...'.format(pathid))
                data, source = this_slave.sock.recvfrom(65535)
                print('debug: got a packetat Path{0}...'.format(pathid))
                this_segment = SEGMENT.decap(
                    data.decode())  # decap the data, the data is encoded and need to be decoded
                this_segment.showseg('')
                buffer.put((this_segment.pkt_seq, this_segment.encap()))
                # buffer.put_segment_and_encap(this_segment)
                if this_segment.pkt_type == _pTYPES.END or this_segment.pkt_type == _pTYPES.END_OF_SLAVE:
                    break

    def waiting_for_order(self):
        while True:
            print('debug: Master is waiting for order...')
            recv_packet = self.master.recv(65535).decode()
            print(recv_packet)
            segment = SEGMENT.decap(recv_packet)
            if segment.pkt_type == _pTYPES.REQUEST_TO_ADD_SLAVE:
                print('debug: sending message to add slave...')
                self.add_slave(segment.pathid, ('127.0.0.1', 9880 + segment.pathid))
                self.slave_offset += 1
            else:
                if segment.pkt_type == _pTYPES.KILL_MASTER:
                    segment = SEGMENT(_pTYPES.KILL_MASTER, 0, 0, 0, 0, 0,
                                      '')  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
                    send_packet = segment.encap()  # 打包并发出
                    self.master.send(send_packet.encode())
                    print('debug: Long live the Soviet!!!')
                    break
            if self.slave_offset == 3:
                     print('debug: getting outta waiting_for_order()..')
                     break  # 暂时先用着 还没搞定怎么结束
        print('debug: No longer waiting, Master is dead...')


#  发送REQUEST并获得tuple 1. 等待获得数据。 2. 计时
# class Slave_UDP:
#     def __init__(self, slave_tuple: tuple, pathid: int):
#         """
#
#         :type pathid: int
#         """
#         self.slave = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         self.slave.bind(slave_tuple)
#         self.pathid = pathid
#         print('debug:Binding UDP on %s ...'.format(slave_tuple))
#
#     def grabdata(self, buffer: BUFFER):
#         """
#
#         :type buffer: BUFFER
#         """
#         assert isinstance(buffer, BUFFER)
#         while True:
#             data, source = self.slave.recvfrom(65535)
#             segmnt = SEGMENT.decap(data.decode())  # decap the data, the data is encoded and need to be decoded
#             segmnt.showseg('all')
#             # BUFFER用QUEUE来实现
#             buffer.put_segment_and_encap(segmnt)


m = Master_TCP()
m.handshake(('127.0.0.1', 9880))
t_master = Thread(target=m.waiting_for_order, daemon=True)
t_master.start()
t_master.join()

data_segment = []
pathids = list(m.slaves.keys())
slave_post_office = []
for pathid in pathids:
    t_slave_grab_data = Thread(target=m.grabdata, args=(pathid, m.buffer))
    slave_post_office.append(t_slave_grab_data)
for slave in slave_post_office:
    slave.start()
time.sleep(3)
#for slave in slave_post_office:
 #   slave.join()
#m.grabdata(1, m.buffer)
seq = 0
while not m.buffer.empty():
    this_seq, this_segment = m.buffer.get()
    if seq != this_seq:
        print('should be {0} but {1}'.format(seq, this_seq))
    seq += 1
    data_segment.append(SEGMENT.decap(this_segment).pkt_data)

data = str.join('', data_segment)
with open('recv.txt', 'w') as file:
    file.write(data)

print('done!')
# m.slave_run(0)

# assert master != -1
# master.connect(('127.0.0.1', 9880))
# master.send('GET /data.txt')
# data = master.recv(65535)  # data='127.0.0.1:9881'
# slave_tuple = (data.split(':')[0], data.split(':')[1])  # data will be sent here
# # 使用线程接收数据，并且实现端口支持从master获取控制信息。数据
# # master循环接收来自服务器端的反馈
# buffer = PriorityQueue()
