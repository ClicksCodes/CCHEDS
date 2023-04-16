from PIL import Image
import base64 as b64
from math import sqrt, ceil

VERSION=1

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

def best_multiple(n):
    print(f"N {n}")
    square = ceil(sqrt(n))
    best = (square, square)
    # Find the lowest set of factors that gives a value equal to or higher than n
    for i in range(1, n + 1):
        if n % i == 0:
            if i >= square:
                best = (i, n // i)
                break
    return best

class CCHEDS:
    colors = "KBGCRMYW"
    text = ""
    error_correction_mod = [[],[]]
    error_correction_hamming = [[],[]]
    encoded_error_correction = []
    encoded = []
    encode_3s = []
    size = (0, 0)
    parity_color = (0, 0, 0)
    raw_image = None

    def __init__(self, colors:dict=dict({
        "K": (0, 0, 0),
        "B": (0, 0, 255),
        "G": (0, 255, 0),
        "C": (0, 255, 255),
        "R": (255, 0, 0),
        "M": (255, 0, 255),
        "Y": (255, 255, 0),
        "W": (255, 255, 255)
    }), text:str=None):
        self.colors = "".join(colors.keys())
        self.text = text

    def letter_to_rgb(self, letter):
        index = self.colors.index(letter)
        i = bin(index)[2:].zfill(3)
        return tuple([255 if int(n) else 0 for n in i])

    def encode_to_3s(self, string):
        base64encoded = b64.b64encode(string)
        l = []
        for char in base64encoded:
            c = bin(char)
            l.append(c.replace("0b", "").zfill(8))
        t = ("".join(l))
        s = split(t, 3)
        self.encode_3s = s
        self.size = best_multiple(len(s))
        print(self.size)
        return self

    def get_error_correction(self):
        rows = []
        cols = []
        for bits_3 in range(len(self.encode_3s)):
            x = bits_3 % self.size[0]
            if len(cols) <= x:
                cols.append(0)
            cols[x] += int(self.encode_3s[bits_3], 2)

            y = bits_3 // self.size[1]
            if len(rows) <= y:
                rows.append(0)
            rows[y] += int(self.encode_3s[bits_3], 2)
        rows = [i % 64 for i in rows]
        cols = [i % 64 for i in cols]
        self.error_correction_mod[0] = [oct(i)[2:].zfill(4) for i in rows]
        self.error_correction_mod[1] = [oct(i)[2:].zfill(4) for i in cols]
        return self

    def encode_to_letters(self):
        self.encoded = [self.colors[int(i, 2)] for i in self.encode_3s]
        self.error_correction_mod[0] = [[self.colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction_mod[0]]
        self.error_correction_mod[1] = [[self.colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction_mod[1]]
        self.parity_color = self.letter_to_rgb(self.colors[sum(self.colors.index(i) for i in self.encoded) % 8])
        return self

    def encode(self):
        self.encode_to_3s(self.text.encode("utf-8"))
        self.get_error_correction()
        self.encode_to_letters()
        return self

    def _add_meta(self, img):
        size = img.size
        # Version Colors
        octal = int(oct(VERSION)[2:])
        version_colors = [
            letter_to_rgb(colors[octal & 0b111]),
            letter_to_rgb(colors[(octal >> 3) & 0b111]),
        ]

        # Top Left Align
        img.putpixel((0, 0), (0, 0, 0))
        img.putpixel((1, 0), (0, 0, 255))
        img.putpixel((0, 1), (0, 255, 255))
        img.putpixel((1, 1), (0, 255, 0))
        # Top Right MetaData
        img.putpixel((size[0] + 3, 0), version_colors[0])
        img.putpixel((size[0] + 2, 0), (0, 0, 0))
        img.putpixel((size[0] + 3, 1), version_colors[1])
        img.putpixel((size[0] + 2, 1), self.parity_color)
        # Bottom Left Align
        img.putpixel((0, size[1] + 3), (255, 0, 255))
        img.putpixel((1, size[1] + 3), (255, 0, 0))
        img.putpixel((0, size[1] + 2), (0, 0, 0))
        img.putpixel((1, size[1] + 2), (0, 0, 255))
        # Bottom Right Align
        img.putpixel((size[0] + 3, size[1] + 3), (255, 0, 0))
        img.putpixel((size[0] + 2, size[1] + 3), (255, 0, 255))
        img.putpixel((size[0] + 3, size[1] + 2), (255, 255, 255))
        img.putpixel((size[0] + 2, size[1] + 2), (255, 255, 0))
        return img

    def to_image(self):
        size = self.size
        img = Image.new("RGB", (size[0] + 4, size[1] + 4), (0, 0, 0))
        img = self._add_meta(img)

        # Data
        for i in range(len(self.encoded)):
            x = i % size[0]
            y = i // size[1]
            print(x, y, self.encoded[i])
            img.putpixel((x + 2, y + 2), self.letter_to_rgb(self.encoded[i]))

        # Error Correction Mod
        for i in range(len(self.error_correction_mod[0])):
            y = i % size[1]
            img.putpixel((0, y + 2), self.letter_to_rgb(self.error_correction_mod[0][i][0]))
            img.putpixel((1, y + 2), self.letter_to_rgb(self.error_correction_mod[0][i][1]))

        for i in range(len(self.error_correction_mod[1])):
            x = i % size[0]
            img.putpixel((x + 2, 0), self.letter_to_rgb(self.error_correction_mod[1][i][0]))
            img.putpixel((x + 2, 1), self.letter_to_rgb(self.error_correction_mod[1][i][1]))

        # Error Correction Hamming
        # img.putpixel((size + 2, y + 2), letter_to_rgb(self.error_correction_mod[0][i][2]))
        # img.putpixel((size + 3, y + 2), letter_to_rgb(self.error_correction_mod[0][i][3]))
        # img.putpixel((x + 2, size + 2), letter_to_rgb(self.error_correction_mod[1][i][2]))
        # img.putpixel((x + 2, size + 3), letter_to_rgb(self.error_correction_mod[1][i][3]))


        self.raw_image = img
        return self

    def _resize(self, block_size):
        if not self.raw_image:
            self.to_image()
        size = ((self.size[0] + 4) * block_size, (self.size[1] + 4) * block_size)
        img = Image.new("RGB", size, (0, 0, 0))
        img.paste(self.raw_image.resize(size, Image.NEAREST), (0, 0))
        return img

    def save(self, path, block_size=16):
        self._resize(block_size).save(path)
        return self

    def show(self, block_size=16):
        self._resize(block_size).show()
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
    c.set_text().show(64)
