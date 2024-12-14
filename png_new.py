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
        diff = self.width * 3
        
        recon = b''
        ptr = 0
        for row in range(self.height):
            filter_type = img_data[ptr]
            ptr += 1

            #recon += int.to_bytes(filter_type, 'big')
            recon += filter_type
            self.img.append([])
            for col in range(self.width):
                r, g, b = img_data[ptr], img_data[ptr+1], img_data[ptr+2]

                match filter_type:
                    case 1:
                        if col > 0:
                            r += recon[ptr-3]
                            g += recon[ptr-2]
                            b += recon[ptr-1]
                    case 2:
                        if row > 0:
                            r += recon[ptr-1-diff]
                            g += recon[ptr-diff]
                            b += recon[ptr-diff+1]
                    case 3:
                        if row > 0 and col > 0:
                            r = r + math.floor((recon[ptr-3] + recon[ptr-1-diff]) // 2)
                            g = g + math.floor((recon[ptr-2] + recon[ptr-diff]) // 2)
                            b = b + math.floor((recon[ptr-1] + recon[ptr-diff+1]) // 2)
                        elif row > 0:
                            r = r + math.floor(recon[ptr-1-diff] // 2)
                            g = g + math.floor(recon[ptr-diff] // 2)
                            b = b + math.floor(recon[ptr-diff+1] // 2)
                        elif col > 0:
                            r = r + math.floor(recon[ptr-3] // 2)
                            g = g + math.floor(recon[ptr-2] // 2)
                            b = b + math.floor(recon[ptr-1] // 2)
                    case 4:
                        rgb = [r, g, b]
                        for i in range(3):
                            p = 0 
                            if row > 0 and col > 0: # c
                                p -= recon[ptr-2-diff+i]
                            if row > 0: # b
                                p += recon[ptr-1-diff+i]
                            if col > 0: # a
                                p += recon[ptr-3+i]
                            
                            pa = abs(p - recon[ptr-3+i])
                            pb = abs(p - recon[ptr-1-diff+i])
                            pc = abs(p - recon[ptr-2-diff+i])
                            
                            if pa <= pb and pa <= pc:
                                rgb[i] += recon[ptr-3+i]
                            elif pb <= pc:
                                rgb[i] += recon[ptr-1-diff+i]
                            else:
                                rgb[i] += recon[ptr-2-diff+i]
                        
                        r, g, b = rgb[0], rgb[1], rgb[2]

                recon += int.to_bytes(r, 'big') + int.to_bytes(g, 'big') + int.to_bytes(b, 'big')
                self.img[row].append([r, g, b])

                ptr += 3
        print("height:", len(self.img), "width:", len(self.img[0]))

    def save_rgb(self, file_name, rgb_option):
        pass


if __name__ == "__main__":
   f = sys.argv[1]
   obj = PNG()
   obj.load_file(f)
   obj.read_header()
   obj.read_chunks()