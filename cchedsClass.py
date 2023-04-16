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
    error_correction = [[],[]]
    encoded_error_correction = []
    encoded = []
    encode_3s = []
    size = 0
    parity_color = (0, 0, 0)
    raw_image = None

    def __init__(self, text=None):
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
        rows = []
        cols = []
        for i in range(len(self.encode_3s)):
            x = i % self.size
            if len(cols) <= x:
                cols.append(0)
            cols[x] += int(self.encode_3s[i], 2)

            y = i // self.size
            if len(rows) <= y:
                rows.append(0)
            rows[y] += int(self.encode_3s[i], 2)
        rows = [i % 4096 for i in rows]
        cols = [i % 4096 for i in cols]
        print(cols)
        self.error_correction[0] = [oct(i)[2:].zfill(4) for i in rows]
        self.error_correction[1] = [oct(i)[2:].zfill(4) for i in cols]
        print(self.error_correction[1])
        return self

    def encode_to_letters(self):
        self.encoded = [colors[int(i, 2)] for i in self.encode_3s]
        self.error_correction[0] = [[colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction[0]]
        self.error_correction[1] = [[colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction[1]]
        self.parity_color = letter_to_rgb[colors[sum(letters_to_int[i] for i in self.encoded) % 8]]
        return self

    def encode(self):
        self.encode_to_3s(self.text.encode("utf-8"))
        self.get_error_correction()
        self.encode_to_letters()
        return self


    def to_image(self):
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

        # Data
        for i in range(len(self.encoded)):
            x = i % size
            y = i // size
            img.putpixel((x + 2, y + 2), letter_to_rgb[self.encoded[i]])

        # Error Correction
        for i in range(len(self.error_correction[0])):
            y = i % size
            img.putpixel((0, y + 2), letter_to_rgb[self.error_correction[0][i][0]])
            img.putpixel((1, y + 2), letter_to_rgb[self.error_correction[0][i][1]])
            img.putpixel((size + 2, y + 2), letter_to_rgb[self.error_correction[0][i][2]])
            img.putpixel((size + 3, y + 2), letter_to_rgb[self.error_correction[0][i][3]])

        for i in range(len(self.error_correction[1])):
            x = i % size
            img.putpixel((x + 2, 0), letter_to_rgb[self.error_correction[1][i][0]])
            img.putpixel((x + 2, 1), letter_to_rgb[self.error_correction[1][i][1]])
            img.putpixel((x + 2, size + 2), letter_to_rgb[self.error_correction[1][i][2]])
            img.putpixel((x + 2, size + 3), letter_to_rgb[self.error_correction[1][i][3]])

        self.raw_image = img
        return self

    def resize(self, size):
        if not self.raw_image:
            self.to_image()
        img = Image.new("RGB", (size, size), (0, 0, 0))
        img.paste(self.raw_image.resize((size, size), Image.NEAREST), (0, 0))
        return img

    def save(self, path, size=256):
        self.resize(size).save(path)
        return self

    def show(self, size=256):
        self.resize(size).show()
        return self

    def set_text(self, Text=None):
        if not Text:
            self.text = input("Text: ")
        else:
            self.text = Text
        self.encode()
        return self


if __name__ == "__main__":
    c = CCHEDS()
    c.set_text().show()