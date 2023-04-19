import base64 as b64
import os
import time
from math import ceil
import cv2
import numpy as np
from PIL import Image

import xxhash as xxh
from PIL import Image

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
    text: bytes = b""
    letter_to_rgb = lambda letter: (0, 0, 0)

    size = (0, 0)
    raw_data = []
    hash_bytes = b""

    def __init__(self, colors: dict or callable = None, text: bytes = None):
        if type(colors) == callable:
            self.letter_to_rgb = colors
        elif type(colors) == dict:
            self.letter_to_rgb = lambda letter: colors[letter]
        else:
            self.letter_to_rgb = lambda letter: tuple([255 if int(n) else 0 for n in "".join(letter)])
        self.text = text

    def encode(self, hash_algorithm=0):
        # Construct the hash of the data
        if hash_algorithm == 0:
            hasher = xxh.xxh64()
            hasher.update(self.text)
            self.hash_bytes = hasher.digest()
            self.hash_bytes = b64.b64encode(self.hash_bytes)
        self.hash_bytes = "".join([bin(n)[2:].zfill(8) for n in self.hash_bytes])
        # Encode the data through base64
        self.text = b64.b64encode(self.text)
        # Then convert it to 3 bit binary
        self.text = "".join([bin(n)[2:].zfill(8) for n in self.text])
        data_size = ceil(len(self.text) / 3)
        # Find the best size of the image
        self.size = best_multiple(data_size)
        # Create a 2D array of 0s with the size of the image
        self.raw_data = [[0 for _ in range(self.size[0] + 4)] for _ in range(self.size[1] + 4)]
        # Split the data into 3 bit chunks
        self.text_split = split(self.text, 3)
        # Convert each 3 bit chunk into a number from 0-7 (binary)
        self.text_split = [int(n, 2) for n in self.text_split]
        # Store this in a 2D array
        for column in range(self.size[0]):
            for row in range(self.size[1]):
                index = row * self.size[0] + column
                if index < len(self.text_split):
                    self.raw_data[row + 2][column + 2] = self.text_split[index]

        # Add alignment squares
        self.raw_data[0][:2] = [0, 1]  # Top left, top row
        self.raw_data[1][:2] = [3, 2]  # Top left, bottom row
        self.raw_data[-2][:2] = [0, 1]  # Bottom left, top row
        self.raw_data[-1][:2] = [5, 4]  # Bottom left, bottom row
        self.raw_data[-1][-2:] = [5, 4]  # Bottom right, bottom row
        self.raw_data[-2][-2:] = [6, 7]  # Bottom right, top row

        # Add version
        self.raw_data[0][-1] = VERSION % 8  # Top right, top right
        self.raw_data[1][-1] = VERSION // 8  # Top right, bottom right

        # Perform checksums on the rows and columns, as well as the parity bit
        self._add_checksums(hash_algorithm)
        self.stored_data = " ".join(["".join([str(r) for r in n]) for n in self.raw_data.copy()])

    def _add_checksums(self, hash_algorithm: int = 0):
        # Checksum
        row_sums = []
        column_sums = []
        for row in self.raw_data:
            row_sums.append(sum(row))
        for column in range(len(self.raw_data[0])):
            column_sums.append(sum([row[column] for row in self.raw_data]))
        row_sums, column_sums = [n % 64 for n in row_sums], [n % 64 for n in column_sums]
        overall_sum = sum(row_sums) + sum(column_sums)
        overall_sum %= 8
        # Trim the first and last 2 rows and columns
        row_sums, column_sums = row_sums[2:-2], column_sums[2:-2]
        # Add the checksums to the image
        for row in range(len(row_sums)):
            self.raw_data[row + 2][0] = row_sums[row] % 8
            self.raw_data[row + 2][1] = row_sums[row] // 8
        for column in range(len(column_sums)):
            self.raw_data[0][column + 2] = column_sums[column] % 8
            self.raw_data[1][column + 2] = column_sums[column] // 8
        self.raw_data[1][-2] = overall_sum
        # Hash
        # The first {height} bits of the hash are stored on the right, then along the bottom
        # Extra characters are ignored, missing characters are 0s (default)
        # Split the hash into 3 bit chunks
        self.hash_bytes = split(self.hash_bytes, 3)
        if len(self.hash_bytes) < 2 * (self.size[0] + self.size[1]):
            self.hash_bytes += ["0" * 3] * (self.size[0] + self.size[1] - len(self.hash_bytes))
        cutoff = (2 * self.size[0]) - 2
        for pixel_index in range(len(self.hash_bytes)):
            if pixel_index < cutoff:
                # The pixel should be on the right
                x = self.size[0] + 2 + (pixel_index % 2)
                y = 2 + (pixel_index // 2)
            else:
                # The pixel should be on the bottom
                x = (pixel_index - cutoff) % self.size[0] + 2
                y = self.size[1] + 2 + (pixel_index - cutoff) // self.size[0]
            if x > self.size[0] + 3 or y > self.size[1] + 3:
                break
            self.raw_data[y][x] = int(self.hash_bytes[pixel_index], 2)
        # Set the hash algorithm pixel
        self.raw_data[0][-2] = hash_algorithm

    def _get_image(self, scale_factor: int = 1):
        # Convert the raw data to RGB tuples using the letter_to_rgb function
        self.raw_data = [[self.letter_to_rgb(bin(n)[2:].zfill(3)) for n in row] for row in self.raw_data]
        # Create a CV2 image from the data
        image = np.array(self.raw_data, dtype=np.uint8)
        if scale_factor > 1:
            # Resize multiple of the actual size (no interpolation)
            image = cv2.resize(image, (self.size[0] * scale_factor, self.size[1] * scale_factor), interpolation=cv2.INTER_NEAREST)
        im = Image.fromarray(image)
        return im

    def show(self, scale: bool = False):
        image = self._get_image(100 if scale else 1)
        image.show()

    def save(self, filename: str = "CCHEDS.png", scale: bool = False):
        image = self._get_image(100 if scale else 1)
        image.save(filename)

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
    c.set_text()
    action = input("[V]iew, Output [T]ext, [S]ave: ")
    if "t" in action.lower():
        print(c.stored_data)
    if "s" in action.lower():
        c.save(input("Filename: "))
    if "v" in action.lower():
        c.show(True)
