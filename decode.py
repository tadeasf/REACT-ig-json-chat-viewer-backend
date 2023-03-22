import os
import json
from decoder_very_fast import FacebookIO


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


def decode_json_files(input_folder, output_folder):
    file_list = [filename for filename in os.listdir(
        input_folder) if filename.endswith(".json")]

    for filename in file_list:
        input_file_path = os.path.join(input_folder, filename)
        output_file_path = os.path.join(output_folder, filename)

        with FacebookIO(input_file_path, 'rb') as f:
            d = json.load(f)

        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            json.dump(d, outfile, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    input_folder = 'in/'  # folder with json files
    output_folder = 'out/'  # folder for the decoded output files
    decode_json_files(input_folder, output_folder)
