from PIL import Image
import base64 as b64
from math import sqrt, ceil

VERSION=0

colors_arr = "KBGCRMYW"

def letter_to_rgb(letter):
    index = colors_arr.index(letter)
    i = bin(index)[2:].zfill(3)
    return [255 if int(n) else 0 for n in i]

def next_perfect_square(n):
    return ceil(sqrt(n))

def split(bytes, number):
    l = []
    s = ""
    i = 0
    m = 0
    for b in bytes:
        s += b
        i += 1
        m += 1
        if i == number:
            l.append(s)
            s = ""
            i = 0
        if m == len(bytes):
            if(len(s) < number):
                s = s.ljust(number, "0")
            l.append(s)
    return l


def encode_to_3s(data):
    base64encoded = b64.b64encode(data)
    l = []
    for char in base64encoded:
        c = bin(char)
        l.append(c.replace("0b", "").zfill(8))
    t = ("".join(l))
    s = split(t, 3)
    return s

def encode_to_letters(data):
    return [bin(i)[2:].zfill(3) for i in data]

def decode_from_string(data):
    s = "".join(data)
    l = split(s, 8)
    l = [chr(int(i, 2)) for i in l]
    decoded = b64.b64decode("".join(l))
    return decoded

def decode_from_letters(string_arr):
    s = "".join(string_arr)
    s = s.replace("K", "000")
    s = s.replace("B", "001")
    s = s.replace("G", "010")
    s = s.replace("C", "011")
    s = s.replace("R", "100")
    s = s.replace("M", "101")
    s = s.replace("Y", "110")
    s = s.replace("W", "111")
    return s

def get_error_correction(data):
    i = 0
    for l in data:
        i += colors_arr.index(l)
    return data

def to_image(data, final_size=(256,256)):
    size = next_perfect_square(len(data))
    img = Image.new("RGB", (size + 4, size + 4), "black")

    octal = int(oct(VERSION)[2:])
    version_colors = [
        letter_to_rgb(colors_arr[octal & 0b111]),
        letter_to_rgb(colors_arr[(octal >> 3) & 0b111]),
    ]
    parity_color = (0, 0, 0)
    # Top Left Align
    img.putpixel((0, 0), (0, 0, 0))
    img.putpixel((1, 0), (0, 0, 255))
    img.putpixel((0, 1), (0, 255, 255))
    img.putpixel((1, 1), (0, 255, 0))
    # Top Right MetaData
    img.putpixel((size + 3, 0), version_colors[0])
    img.putpixel((size + 2, 0), (0, 0, 0))
    img.putpixel((size + 3, 1), version_colors[1])
    img.putpixel((size + 2, 1), parity_color)
    # Bottom Left Align
    img.putpixel((0, size + 3), (255, 0, 255))
    img.putpixel((1, size + 3), (255, 0, 0))
    img.putpixel((0, size + 2), (0, 0, 0))
    img.putpixel((1, size + 2), (0, 0, 255))
    # Bottom Right Align
    img.putpixel((size + 3, size + 3), (255, 0, 0))
    img.putpixel((size + 2, size + 3), (255, 0, 255))
    img.putpixel((size + 3, size + 2), (255, 255, 255))
    img.putpixel((size + 2, size + 2), (255, 255, 0))

    # Data
    for i in range(len(data)):
        x = i % size
        y = i // size
        img.putpixel((x + 2, y + 2), letter_to_rgb(data[i]))

    # Error Correction
    # for i in range(len(data.error_correction)):
    #     ...

    # Show/Save
    img.resize(final_size, Image.Resampling.BOX).show()


def main():
    a = encode_to_3s("Hello World".encode("utf-8"))
    print(a, len(a))
    b = encode_to_letters(a)
    print(b, len(b))
    to_image(b)
    c = decode_from_letters(b)
    print(c, len(c))
    d = decode_from_string(c)
    print(d)




if __name__ == "__main__":
    main()