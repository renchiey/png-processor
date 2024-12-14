import math
import zlib
import sys

class PNG:
    def __init__(self):
        self.data = b''
        self.info = ''
        self.width = 0
        self.height = 0
        self.bit_depth = 0
        self.color_type = 0
        self.compress = 0
        self.filter = 0
        self.interlace = 0
        self.img = []

    def load_file(self, file_name):
        try:
            with open(file_name, 'rb') as file:
                self.data = file.read()
            self.info = file_name
        except FileNotFoundError:
            self.info = 'file not found'

    def valid_png(self):
        return self.data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')

    def read_header(self):
        if not self.valid_png():
            raise ValueError('Not a valid PNG file')

        #data_length = self.data[8:12]
        ihdr_data = self.data[16:29]
        self.width = int.from_bytes(ihdr_data[0:4], 'big')
        self.height = int.from_bytes(ihdr_data[4:8], 'big')
        self.bit_depth = ihdr_data[8]
        self.color_type = ihdr_data[9]
        self.compress = ihdr_data[10]
        self.filter = ihdr_data[11]
        self.interlace = ihdr_data[12]

        if (self.bit_depth != 8 or self.color_type != 2 or self.compress != 0 or 
                self.filter != 0 or self.interlace != 0):
            raise ValueError('Unsupported PNG format specifications')

        print(self.width, self.height, self.bit_depth, self.color_type, self.compress, self.filter, self.interlace)

    def read_chunks(self):
        if not self.valid_png():
            raise ValueError('Not a valid PNG file')

        pos = 29  # after IHDR chunk
        compressed_data = b''

        IDAT = b'\x49\x44\x41\x54'
        IEND = b'\x49\x45\x4E\x44'

        match_ptr = 0

        flag = False

        # extract image data from datastream
        while pos < len(self.data):
   
            while match_ptr < len(IDAT) and self.data[pos] == IDAT[match_ptr]:
                match_ptr += 1
                pos += 1
                flag = True

            if match_ptr == len(IDAT):
                chunk_length = int.from_bytes(self.data[pos-8:pos-4], 'big')

                compressed_data += self.data[pos:pos+chunk_length]
                pos += chunk_length

            elif match_ptr == 1:
                while match_ptr < len(IEND) and self.data[pos] == IEND[match_ptr]:
                    match_ptr += 1
                    pos += 1
                
                if match_ptr == len(IEND):
                    break
    
            match_ptr = 0
            if not flag:
                pos += 1
            flag = False


        try:
            img_data = zlib.decompress(compressed_data)
        except zlib.error:
            raise ValueError('Decompression failed')
        
        # process image data
        
        ptr = 0
        for row in range(self.height):
            filter_type = img_data[ptr]
            ptr += 1

            self.img.append([])
            for col in range(self.width):
                r, g, b = img_data[ptr], img_data[ptr+1], img_data[ptr+2]

                match filter_type:
                    case 1:
                        if col > 0:
                            r += img_data[ptr-3]
                            g += img_data[ptr-2]
                            b += img_data[ptr-1]
                    case 2:
                        if row > 0:
                            diff = self.width * 3
                            r += img_data[ptr-1-diff]
                            g += img_data[ptr-diff]
                            b += img_data[ptr-diff+1]
                    case 3:
                        if row > 0 and col > 0:
                            r = r + math.floor((img_data[ptr-3] + img_data[ptr-1-diff]) // 2)
                            g = g + math.floor((img_data[ptr-2] + img_data[ptr-diff]) // 2)
                            b = b + math.floor((img_data[ptr-1] + img_data[ptr-diff+1]) // 2)
                        elif row > 0:
                            r = r + math.floor(img_data[ptr-1-diff] // 2)
                            g = g + math.floor(img_data[ptr-diff] // 2)
                            b = b + math.floor(img_data[ptr-diff+1] // 2)
                        elif col > 0:
                            r = r + math.floor(img_data[ptr-3] // 2)
                            g = g + math.floor(img_data[ptr-2] // 2)
                            b = b + math.floor(img_data[ptr-1] // 2)
                    case 4:
                        # p = a + b - c
                        # pa = abs(p - a)
                        # pb = abs(p - b)
                        # pc = abs(p - c)
                        # if pa <= pb and pa <= pc then Pr = a
                        # else if pb <= pc then Pr = b
                        # else Pr = c
                        pass

                img_data[ptr], img_data[ptr+1], img_data[ptr+2] = r, g, b
                self.img[row].append([r, g, b])

                ptr += 3
                     



    def process_image_data(self, img_data):
        pass

    def save_rgb(self, file_name, rgb_option):
        pass


if __name__ == "__main__":
   #f = sys.argv[1]
   #obj = PNG()
   #obj.load_file(f)
   #obj.read_header()
   #obj.read_chunks()
   #obj.save_rgb('new_png.png', 1)

    with open("test.txt", 'rb') as f:
        data = f.read()
        print(len(data))