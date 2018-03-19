from queue import PriorityQueue


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
