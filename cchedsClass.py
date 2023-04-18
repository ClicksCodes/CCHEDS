from PIL import Image
import base64 as b64
from math import ceil
import xxhash as xxh
import os

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

def get_terminal_width():
    return int(os.get_terminal_size().columns)

def best_multiple(n):
    print("Finding best multiple for:", n)
    terminal_width = get_terminal_width()
    # Find all the factors of n
    factors = set()
    for width in range(1, n + 1):
        min_height = ceil(n / width)
        factors.add((max(width, min_height), min(width, min_height)))
    # Calculate ranks for each, lower is better
    ranks = {k: 1 for k in list(factors)}
    for i, factor in enumerate(ranks):
        print("#" * int((i / len(ranks)) * terminal_width), end="\r")
        ranks[factor] *= ((factor[0] - factor[1]) ** 2) + 1
        ranks[factor] += (factor[0] * factor[1]) - n
    print("Processed all factors ")
    minimum = min(ranks.values())
    all_with_lowest = [k for k, v in ranks.items() if v == minimum]
    return all_with_lowest[0]

class CCHEDS:
    colors = "KBGCRMYW"
    text: bytes = b""
    error_correction_mod = [[],[]]
    encoded_error_correction = []
    encoded = []
    encode_3s = []
    hash_3s = []
    hash_encoded = []
    size = (0, 0)
    parity_color = (0, 0, 0)
    raw_image = None
    letter_to_rgb = lambda letter: (0, 0, 0)

    def __init__(self, colors: dict or callable = None, color_names: str = "KBGCRMYW", text: bytes = None):
        self.colors = color_names
        if type(colors) == callable:
            self.letter_to_rgb = colors
        elif type(colors) == dict:
            self.letter_to_rgb = lambda letter: colors[letter]
        else:
            self.letter_to_rgb = lambda letter: tuple([255 if int(n) else 0 for n in bin(self.colors.index(letter))[2:].zfill(3)])
        self.text = text

    def _encode_to_3s(self, string, find_size=False):
        base64encoded = b64.b64encode(string)
        l = []
        for char in base64encoded:
            c = bin(char)
            l.append(c.replace("0b", "").zfill(8))
        t = ("".join(l))
        s = split(t, 3)
        if find_size:
            self.size = best_multiple(len(s))
        return s

    def _get_error_correction(self):
        rows = []
        cols = []
        for bits_3 in range(len(self.encode_3s)):
            x = bits_3 % self.size[0]
            if len(cols) <= x:
                cols.append(0)
            cols[x] += int(self.encode_3s[bits_3], 2)

            y = bits_3 // self.size[0]
            if len(rows) <= y:
                rows.append(0)
            rows[y] += int(self.encode_3s[bits_3], 2)
        rows = [i % 64 for i in rows]
        cols = [i % 64 for i in cols]
        return [[oct(i)[2:].zfill(4) for i in rows], [oct(i)[2:].zfill(4) for i in cols]]

    def _encode_to_letters(self):
        self.encoded = [self.colors[int(i, 2)] for i in self.encode_3s]
        self.error_correction_mod[0] = [[self.colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction_mod[0]]
        self.error_correction_mod[1] = [[self.colors[int(j, 8)] for j in i[::-1]] for i in self.error_correction_mod[1]]
        self.parity_color = self.letter_to_rgb(self.colors[sum(self.colors.index(i) for i in self.encoded) % 8])
        self.hash_encoded = [self.colors[int(i, 2)] for i in self.hash_3s]
        return self

    def encode(self):
        hasher = xxh.xxh64()
        hasher.update(self.text)
        hasher = hasher.digest()
        self.hash_3s = self._encode_to_3s(hasher)
        self.encode_3s = self._encode_to_3s(self.text, True)
        self.error_correction_mod = self._get_error_correction()
        self._encode_to_letters()
        return self

    def _add_meta(self, img):
        size = self.size
        # Version Colors
        octal = int(oct(VERSION)[2:])
        version_colors = [
            self.letter_to_rgb(self.colors[octal & 0b111]),
            self.letter_to_rgb(self.colors[(octal >> 3) & 0b111]),
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

    def _to_image(self):
        size = self.size
        img = Image.new("RGB", (size[0] + 4, size[1] + 4), (0, 0, 0))
        img = self._add_meta(img)
        terminal_width = get_terminal_width()

        # Data
        for i in range(len(self.encoded)):
            x = i % size[0]
            y = i // size[0]
            img.putpixel((x + 2, y + 2), self.letter_to_rgb(self.encoded[i]))
            print("#" * round((i / len(self.encoded)) * terminal_width), end="\r")
        print("Added data ")

        # Error Correction Mod
        for i in range(len(self.error_correction_mod[0])):
            y = i % size[1]
            img.putpixel((0, y + 2), self.letter_to_rgb(self.error_correction_mod[0][i][0]))
            img.putpixel((1, y + 2), self.letter_to_rgb(self.error_correction_mod[0][i][1]))
            print("#" * round((i / len(self.error_correction_mod[0])) * terminal_width), end="\r")
        print("Added top error correction ")

        for i in range(len(self.error_correction_mod[1])):
            x = i % size[0]
            img.putpixel((x + 2, 0), self.letter_to_rgb(self.error_correction_mod[1][i][0]))
            img.putpixel((x + 2, 1), self.letter_to_rgb(self.error_correction_mod[1][i][1]))
            print("#" * round((i / len(self.error_correction_mod[1])) * terminal_width), end="\r")
        print("Added side error correction ")

        # Hash
        current_string = self.hash_encoded[:2*sum(self.size)]
        for pixel_index in range(len(current_string) // 2):
            x = self.size[0] + 2 + (pixel_index % 2)
            y = 2 + pixel_index // 2
            img.putpixel((x, y), self.letter_to_rgb(current_string[pixel_index]))
            print("#" * round((pixel_index / len(current_string)) * terminal_width), end="\r")
        offset = len(current_string) // 2
        for pixel_index in range(offset, len(current_string)):
            x = (pixel_index % self.size[0]) + 2
            y = self.size[1] + 2 + ((pixel_index - offset) // self.size[0])
            img.putpixel((x, y), self.letter_to_rgb(current_string[pixel_index]))
            print("#" * round((pixel_index / len(current_string)) * terminal_width), end="\r")
        print("Added hash ")

        self.raw_image = img
        return self

    def _resize(self, block_size):
        if not self.raw_image:
            self._to_image()
        print("Resizing")
        size = ((self.size[0] + 4) * block_size, (self.size[1] + 4) * block_size)
        img = Image.new("RGB", size, (0, 0, 0))
        print("Pasting")
        img.paste(self.raw_image.resize(size, Image.NEAREST), (0, 0))
        return img

    def save(self, path, block_size=16):
        self._resize(block_size).save(path)
        return self

    def show(self, block_size=16):
        self._resize(block_size).show()
        return self

    def set_text(self, text=None):
        if not text:
            action = input("[T]ext or [F]ile: ")
            if action.lower() == "f":
                self.text = bytes(open(input("Filename: ")).read(), "utf-8")
            else:
                self.text = bytes(input("Text: "), "utf-8")
        else:
            self.text = bytes(text, "utf-8")
        self.encode()
        return self


if __name__ == "__main__":
    c = CCHEDS()
    c.set_text().show(64)
