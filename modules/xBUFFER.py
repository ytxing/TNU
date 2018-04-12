from queue import PriorityQueue
from TNU.modules.xSEGMENT import SEGMENT


class BUFFER(PriorityQueue):
    def __init__(self):
        super().__init__()
        self.buffer = PriorityQueue(-1)

    def put_segment_and_encap(self, segment):
        """

        :type segment: SEGMENT
        """
        isinstance(segment, SEGMENT)
        self.buffer.put((segment.pkt_seq, SEGMENT.encap(segment)))

    def put_raw_segment(self, segment: SEGMENT):
        """

         :type segment: SEGMENT
        """
        isinstance(segment, SEGMENT)
        self.buffer.put((segment.pkt_seq, segment))

    def show_first_segment(self) -> (int, SEGMENT):  # 返回最小编号包但不从缓存中取出
        (seq, data) = self.get()
        isinstance(data, str)
        self.put(seq, data)
        return seq, data
