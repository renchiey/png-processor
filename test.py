import sys


def read_png(filename):
    try:
        with open(filename, 'rb') as png:
            data = png.read()
            #print(data)
            print(data.startswith(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'))
            print(data[12:16].hex())
    except FileNotFoundError:
        print("File does not exist")


if __name__ == "__main__":
    f = sys.argv[1]
    read_png(f)