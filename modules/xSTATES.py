# -*- coding: utf-8 -*-
class pTYPES:
    CHUNK = 0
    END_OF_SLAVE = 1
    END = 2
    REQUEST_TO_ADD_SLAVE = 3
    RESPONSE_TO_ADD_SLAVE = 4
    REJECT_TO_ADD_SLAVE = 5
    KILL_MASTER = 6
    MASTER_HEARTBEAT = 7
    ACK = 8
    DONE_TRANSMISSION = 9
    I_WANT_DATA = 10
    NO_MORE_SLAVE = 11
    CHUNK_INFO = 12  # total_seq ratio opt'
    OUT_OF_ORDER_PACKET = 13
