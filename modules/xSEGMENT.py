# -*- coding: utf-8 -*-
#from ctypes import c_ulong, c_ulonglong, c_float
import re


class SEGMENT:
    def __init__(self, pkt_type, pkt_seq, pkt_ack, pathid, pkt_ratio, opt, pkt_data):
        """
        encapsulating a SEGMENT
        :type pkt_data: str
        """
        self.pkt_type = int(pkt_type)
        self.pkt_seq = int(pkt_seq)
        self.pkt_ack = int(pkt_ack)
        self.pathid = int(pathid)
        self.pkt_ratio = float(pkt_ratio)
        self.pkt_datalen = int(len(pkt_data))
        self.pkt_data = str(pkt_data)
        self.opt = int(opt)
        # self.pkt_headlen = len('pkt_type:'+ self.pkt_type + '\n'\
        #          'pkt_seq:'+ self.pkt_seq + '\n'\
        #          'pkt_ack:'+ self.pkt_ack + '\n'\
        #          'pkt_ratio:'+ self.pkt_ratio + '\n'\
        #          'option:' + self.opt + '\n'\
        #          'pkt_datalen:'+ self.pkt_datalen + '\n')

    def encap(self) -> str:
        packet = 'pkt_type:'+ str(self.pkt_type) + '\n'\
                 'pkt_seq:'+ str(self.pkt_seq) + '\n'\
                 'pkt_ack:'+ str(self.pkt_ack) + '\n'\
                 'pathid:' + str(self.pathid) + '\n'\
                 'pkt_ratio:'+ str(self.pkt_ratio) + '\n'\
                 'option:' + str(self.opt) + '\n'\
                 'pkt_datalen:'+ str(self.pkt_datalen) + '\n' \
                 'pkt_data:'+ self.pkt_data
        return str(packet)

    @staticmethod
    def decap(packet: str):
        _list = re.split(':|\n',packet, 15)
        # print('debug: decaping\n{}'.format(packet))
        assert isinstance(_list, list)
        assert _list[0] == 'pkt_type'
        assert _list[2] == 'pkt_seq'
        assert _list[4] == 'pkt_ack'
        assert _list[6] == 'pathid'
        assert _list[8] == 'pkt_ratio'
        assert _list[10] == 'option'
        assert _list[12] == 'pkt_datalen'
        # assert _list[13] == str(len(_list[15]))
        assert _list[14] == 'pkt_data'
        segment = SEGMENT(_list[1], _list[3],_list[5],_list[7], _list[9], _list[11], _list[15])

        return segment

    def showseg(self, flag):
        if flag == 'all':
            print('HEADER:\npkt_type:'+ str(self.pkt_type) + '\n'\
                 'pkt_seq:'+ str(self.pkt_seq) + '\n'\
                 'pkt_ack:'+ str(self.pkt_ack) + '\n'\
                 'pkt_ratio:'+ str(self.pkt_ratio) + '\n'\
                'pathid:'+ str(self.pathid) + '\n'\
                 'option:' + str(self.opt) + '\n'\
                 'pkt_datalen:'+ str(self.pkt_datalen) + '\n' \
                 'DATA:\npkt_data:'+ str(self.pkt_data))
        else:
            print('HEADER:\npkt_type:'+ str(self.pkt_type) + '\n'\
                 'pkt_seq:'+ str(self.pkt_seq) + '\n' \
                                                 'pathid:' + str(self.pathid))



