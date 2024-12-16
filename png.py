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
        self.crc_table = []

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
        prev_row = b'\x00\x00\x00' * (self.width+1)
        data_ptr = 0

        for row in range(self.height):
            filter_type = img_data[data_ptr]
            data_ptr += 1

            if filter_type > 4:
                raise ValueError("invalid filter type:", filter_type)

            curr_row = b'\x00\x00\x00'
            row_ptr = 3

            self.img.append([])

            for col in range(self.width):
                r, g, b = img_data[data_ptr], img_data[data_ptr+1], img_data[data_ptr+2]

                match filter_type: 
                    case 1:
                        r += curr_row[row_ptr-3]
                        g += curr_row[row_ptr-2]
                        b += curr_row[row_ptr-1]
                    case 2:
                        r += prev_row[row_ptr]
                        g += prev_row[row_ptr+1]
                        b += prev_row[row_ptr+2]
                    case 3:
                        r = r + math.floor((curr_row[row_ptr-3] + prev_row[row_ptr]) // 2)
                        g = g + math.floor((curr_row[row_ptr-2] + prev_row[row_ptr+1]) // 2)
                        b = b + math.floor((curr_row[row_ptr-1] + prev_row[row_ptr+2]) // 2)
                    case 4:
                        rgb = [r, g, b]

                        for i in range(3):
                            p = curr_row[row_ptr-3+i] + prev_row[row_ptr+i] - prev_row[row_ptr-3+i]
                            a, b, c = curr_row[row_ptr-3+i], prev_row[row_ptr+i], prev_row[row_ptr-3+i] 
                            
                            pa = abs(p - a)
                            pb = abs(p - b)
                            pc = abs(p - c)
                            
                            if pa <= pb and pa <= pc:
                                rgb[i] += a
                            elif pb <= pc:
                                rgb[i] += b
                            else:
                                rgb[i] += c

                        r, g, b = rgb[0], rgb[1], rgb[2]

                r %= 256
                g %= 256
                b %= 256
                curr_row += r.to_bytes(1, 'big') + g.to_bytes(1, 'big') + b.to_bytes(1, 'big')
                self.img[row].append([r, g, b])

                data_ptr += 3
                row_ptr += 3
            prev_row = curr_row

    def save_rgb(self, file_name, rgb_option):
        png = open(file_name, 'wb')

        # PNG signature
        png.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')

        # IHDR chunk
        png.write((13).to_bytes(4, 'big'))              # IHDR data length
 
        IHDR = b'\x49\x48\x44\x52'                   # IHDR chunk type
        IHDR += (self.width).to_bytes(4, 'big')      # width
        IHDR += (self.height).to_bytes(4, 'big')     # height
        IHDR += (self.bit_depth).to_bytes(1, 'big')  # bit depth
        IHDR += (self.color_type).to_bytes(1, 'big') # color type
        IHDR += (self.compress).to_bytes(1, 'big')   # compression method
        IHDR += (self.filter).to_bytes(1, 'big')     # filter method
        IHDR += (self.interlace).to_bytes(1, 'big')  # interlace method

        png.write(IHDR)
        png.write(int.to_bytes(zlib.crc32(IHDR), 4, 'big')) # CRC checksum

        # IDAT chunks
        IDAT_type = b'\x49\x44\x41\x54'

        compress = zlib.compressobj()
        compressed_data = b''
        for row in range(len(self.img)):
            compressed_data += compress.compress(b'\x00')

            for col in range(len(self.img[row])):
                match rgb_option:
                    case 1:
                        compressed_data += compress.compress(int.to_bytes(self.img[row][col][0], 1, 'big') + b'\x00\x00')
                    case 2:
                        compressed_data += compress.compress(b'\x00' + int.to_bytes(self.img[row][col][1], 1, 'big') + b'\x00')
                    case 3:
                        compressed_data += compress.compress(b'\x00\x00' + int.to_bytes(self.img[row][col][2], 1, 'big'))
                    case _:
                        raise IndexError("Invalid RGB option")
        

        png.write(int.to_bytes(len(compressed_data), 4, 'big'))  # IDAT compressed data length
        png.write(IDAT_type)  
        png.write(compressed_data)
        png.write(int.to_bytes(zlib.crc32(IDAT_type + compressed_data), 4, 'big'))

        # IEND chunk
        IEND = b'\x00\x00\x00\x00\x49\x45\x4E\x44'

        png.write(IEND)
        png.write(int.to_bytes(zlib.crc32(IEND[4:]), 4, 'big'))

        png.close()
        
