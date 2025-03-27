from typing import List

class Packet:
    def __init__(self, message_id: int):
        self._bytes = bytearray()
        self._index = 4
        self.msg_id = message_id
        self.write(self.msg_id.to_bytes(4, 'little'))

    def write(self, data: bytes):
        self._bytes += data
        return self

    def write_int(self, integer: int):
        self._bytes += integer.to_bytes(8, 'little')
        return self

    def write_str(self, string: str):
        self.write_int(len(string))
        self.write(string.encode())
        return self

    def write_ints(self, ints: List[int]):
        self.write_int(len(ints))
        for integer in ints:
            self.write_int(integer)
        return self

    def write_strs(self, strs: List[str]):
        self.write_int(len(strs))
        for string in strs:
            self.write_str(string)
        return self

    def seek(self, index: int):
        self._index = index
        return self

    def read(self, amt: int) -> bytes:
        data = self._bytes[self._index:self._index + amt] 
        self._index += amt
        return data
    
    def read_str(self) -> str:
        length = self.read_int()
        string = self.read(length)
        return string.decode('utf8') 

    def read_int(self) -> int:
        return int.from_bytes(self.read(8), 'little')

    def read_float(self) -> float:
        return float(self.read(4))

    def read_ints(self):
        return [self.read_int() for _ in range(self.read_int())]
        
    def read_floats(self, n: int):
        return [self.read_float() for _ in range(n)]
    
    def format_to_send(self):
        return len(self._bytes).to_bytes(4, 'little') + self._bytes

