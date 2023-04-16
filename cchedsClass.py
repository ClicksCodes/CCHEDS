from PIL import Image
import base64 as b64
from math import sqrt, ceil

VERSION=0

colors = ["K", "B", "G", "C", "R", "M", "Y", "W"]
letters_to_int = {
    "K": 0,
    "B": 1,
    "G": 2,
    "C": 3,
    "R": 4,
    "M": 5,
    "Y": 6,
    "W": 7
}
letter_to_rgb = {
    "K": (0, 0, 0),
    "B": (0, 0, 255),
    "G": (0, 255, 0),
    "C": (0, 255, 255),
    "R": (255, 0, 0),
    "M": (255, 0, 255),
    "Y": (255, 255, 0),
    "W": (255, 255, 255),
}


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

def next_perfect_square(n):
    return ceil(sqrt(n))

class CCHEDS:
    text = ""
    error_correction_raw = []
    error_correction_3s = [[],[]]
    error_correction = [[],[]]
    encoded = []
    encode_3s = []
    size = 0
    parity_color = (0, 0, 0)

    def __init__(self, text):
        self.text = text

    def encode_to_3s(self, string):
        base64encoded = b64.b64encode(string)
        l = []
        for char in base64encoded:
            c = bin(char)
            l.append(c.replace("0b", "").zfill(8))
        t = ("".join(l))
        s = split(t, 3)
        self.encode_3s = s
        self.size = next_perfect_square(len(s))
        self.error_correction_raw = [[0 for i in range(4)] for i in range(self.size)]
        return self

    def get_error_correction(self):
        # print(self.error_correction_raw)
        return self

    def encode_to_letters(self):
        self.encoded = [colors[int(i, 2)] for i in self.encode_3s]
        # self.error_correction[0] = [colors[int(i)] for i in self.error_correction_3s[0]]
        # self.error_correction[1] = [colors[int(i)] for i in self.error_correction_3s[1]]
        return self

    def encode(self):
        self.encode_to_3s(self.text.encode("utf-8"))
        self.get_error_correction()
        self.encode_to_letters()
        return self


    def to_image(self, save=False):
        size = self.size
        img = Image.new("RGB", (size + 4, size + 4), (0, 0, 0))

        # Version Colors
        octal = int(oct(VERSION)[2:])
        version_colors = [
            letter_to_rgb[colors[octal & 0b111]],
            letter_to_rgb[colors[(octal >> 3) & 0b111]],
        ]

        # Top Left Align
        img.putpixel((0, 0), (0, 0, 0))
        img.putpixel((1, 0), (0, 0, 255))
        img.putpixel((0, 1), (0, 255, 255))
        img.putpixel((1, 1), (0, 255, 0))
        # Top Right MetaData
        img.putpixel((size + 3, 0), version_colors[0])
        img.putpixel((size + 2, 0), (0, 0, 0))
        img.putpixel((size + 3, 1), version_colors[1])
        img.putpixel((size + 2, 1), self.parity_color)
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

        for i in range(len(self.encoded)):
            x = i % size
            y = i // size
            img.putpixel((x + 2, y + 2), letter_to_rgb[self.encoded[i]])

        img.resize((size * 10, size * 10), Image.Resampling.BOX).show()


if __name__ == "__main__":
    c = CCHEDS("Hello World")
    c.encode()
    c.to_image()