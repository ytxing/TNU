import socket
from TNU.modules._SEGMENT import SEGMENT
from TNU.modules._STATES import _pTYPES
from TNU.modules._BUFFER import BUFFER
from threading import Thread, Event
import time


class slave_config:
    addr = '127.0.0.1'
    port = 9881
    pathid_list = []
    slave_tuple = (addr, port)


class Master_TCP(socket.socket):
    def __init__(self):
        super().__init__()
        self.master = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        assert self.master != -1
        self.buffer = BUFFER()
        self.slaves = {}  # PathID:Slave_UDP

    def handshake(self, server_tuple: tuple):
        self.master.connect(server_tuple)
        print("debug: Connecting to {0} ...".format(server_tuple))

    def add_slave(self, pathid, _slave_tuple):
        """

        :param _slave_tuple: tuple
        :type pathid: int
        """
        # after Server requests to add a slave, master decided that should be _slave_tuple
        assert isinstance(pathid, int)
        if pathid not in slave_config.pathid_list:
            self.slaves[pathid] = Slave_UDP(_slave_tuple, pathid)
            print('debug: PathID {0} is %s ...'.format(_slave_tuple))
            segment = SEGMENT(_pTYPES.RESPONSE_TO_ADD_SLAVE, 0, 0, pathid, 0, 0,
                              '{0},{1}'.format(slave_config.addr, str(
                                  slave_config.port)))  # pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data
            self.master.send(segment.encap().encode())

    def slave_run(self, pathid: int):
        t = Thread(target=self.slaves[pathid].grabdata, args=self.buffer)
        t.start()
        # threading

    def showbuff(self):
        print(self.buffer)





#  发送REQUEST并获得tuple 1. 等待获得数据。 2. 计时
class Slave_UDP:
    def __init__(self, slave_tuple: tuple, pathid: int):
        """

        :type pathid: int
        """
        self.slave = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.slave.bind(slave_tuple)
        self.pathid = pathid
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


m = Master_TCP()
m.handshake(('127.0.0.1',9880))
segment = SEGMENT.decap(m.master.recv(65535).decode())
if segment.pkt_type == _pTYPES.REQUEST_TO_ADD_SLAVE:
    m.add_slave(0,('127.0.0.1',9881))

m.slave_run(0)

# assert master != -1
# master.connect(('127.0.0.1', 9880))
# master.send('GET /data.txt')
# data = master.recv(65535)  # data='127.0.0.1:9881'
# slave_tuple = (data.split(':')[0], data.split(':')[1])  # data will be sent here
# # 使用线程接收数据，并且实现端口支持从master获取控制信息。数据
# # master循环接收来自服务器端的反馈
# buffer = PriorityQueue()
