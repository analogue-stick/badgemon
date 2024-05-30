from app_components.tokens import colors
from struct import pack, unpack_from

COLOURS = colors
COLOURS["bmon_grey"] = (0.9,0.9,0.9)

PATTERNS = {
    "NONE",
    "HEARTS",
    "CARS",
    "BOLTS",
    "LOGO"
}

class Customisation:
    background_col = "bmon_grey"
    pattern = 0

    def serialise(self):
        data = bytearray()
        data += pack('B', len(self.background_col))
        data += self.background_col.encode('utf-8')
        data += pack('B', self.pattern)
        return data

    @staticmethod
    def deserialise(data):
        print(data)
        c = Customisation()
        offset = 0
        name_len = data[offset]
        offset += 1
        c.background_col = data[offset:offset + name_len].decode('utf-8')
        offset += name_len
        c.pattern = data[offset]
        return c
