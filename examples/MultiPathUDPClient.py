import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES

from queue import PriorityQueue
from threading import Thread, Event
import time


class Master_TCP(socket):
    def __init__(self):
        self.master = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.master != -1
        self.buffer = BUFFER()
        self.slaves = {} # PathID:Slave_UDP

    def handshake(self, server_tuple: tuple):
        self.master.connect(server_tuple)
        print("debug: Connecting to {0} ...".format(server_tuple))

    def add_slave(self, pathid, _slave_tuple):
        """

        :param _slave_tuple: tuple
        :type pathid: int
        """
        assert isinstance(pathid, int)
        self.slaves[pathid] = Slave_UDP(_slave_tuple)
        print('debug: PathID {0} is %s ...'.format(_slave_tuple))

    def slave_run(self,pathid: int):
        pass
        # threading


class BUFFER(PriorityQueue):
    def __init__(self):
        super().__init__()
        self.buffer = PriorityQueue(-1)

    def put_segemnt(self, segment):
        """

        :type segment: SEGMENT
        """
        isinstance(segment, SEGMENT)
        self.buffer.put((segment.pkt_seq, segment))


#  发送REQUEST并获得tuple 1. 等待获得数据。 2. 计时
class Slave_UDP:
    def __init__(self, slave_tuple: tuple):
        self.slave = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.slave.bind(slave_tuple)
        print('debug:Binding UDP on %s ...'.format(slave_tuple))

    def grabdata(self, buffer: BUFFER):
        """

        :type buffer: BUFFER
        """
        assert isinstance(buffer, BUFFER)
        while True:
            data, source = self.slave.recvfrom(65535)
            segmnt = SEGMENT.decap(data.decode())  # decap the data, the data is encoded and need to be decoded
            segmnt.showseg('all')
            # BUFFER用QUEUE来实现
            buffer.put_segemnt(segmnt)



# assert master != -1
# master.connect(('127.0.0.1', 9880))
# master.send('GET /data.txt')
# data = master.recv(65535)  # data='127.0.0.1:9881'
# slave_tuple = (data.split(':')[0], data.split(':')[1])  # data will be sent here
# # 使用线程接收数据，并且实现端口支持从master获取控制信息。数据
# # master循环接收来自服务器端的反馈
# buffer = PriorityQueue()
