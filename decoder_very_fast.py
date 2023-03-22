import io
import json


class FacebookIO(io.FileIO):
    def read(self, size: int = -1) -> bytes:
        data: bytes = super(FacebookIO, self).readall()
        new_data: bytearray = bytearray()
        i: int = 0
        while i < len(data):
            if data.startswith(b'\\u00', i):
                u: int = 0
                new_char = bytearray()
                while data.startswith(b'\\u00', i + u):
                    hex = int(data[i+u+4:i+u+6], 16)
                    new_char.append(hex)
                    u += 6

                new_chars = new_char.decode('utf-8').encode('utf-8')
                new_data += new_chars
                i += u
            else:
                new_data.append(data[i])
                i += 1

        return bytes(new_data)


if __name__ == '__main__':
    f = FacebookIO('data.json', 'rb')
    d = json.load(f)
    print(d)
