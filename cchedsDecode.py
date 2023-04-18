import numpy as np
import cv2
import base64 as b64


def render(arr: list[str]) -> None:
    # arr is a list of strings, each string is a row of the image
    # The numbers in the string are the colours of the pixels
    # 0 = black (0, 0, 0), 1 = blue (0, 0, 255), 2 = green (0, 255, 0), 3 = cyan (0, 255, 255)...
    # Show this using cv2

    # Convert the strings to a list of tuples
    number_to_tuple = lambda letter: tuple([255 if int(n) else 0 for n in bin(letter)[2:].zfill(3)])
    arr = [[number_to_tuple(int(letter)) for letter in row] for row in arr]
    arr = [[(i[2], i[1], i[0]) for i in row] for row in arr]
    # Arr is a list of lists of tuples, each tuple is a pixel with an RGB value
    # Convert this to a numpy array
    arr = np.array(arr, dtype=np.uint8)
    # Show the image
    cv2.imshow("Image", arr)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def rotate(arr: list[str]) -> list[str]:
    """Rotate a 2D array 90 degrees clockwise"""
    return ["".join(row) for row in zip(*arr[::-1])]


def flip_horizontal(arr: list[str]) -> list[str]:
    """Flip a 2D array horizontally"""
    return [row[::-1] for row in arr]

def flip_vertical(arr: list[str]) -> list[str]:
    """Flip a 2D array vertically"""
    return arr[::-1]

def flip_diagonal(arr: list[str]) -> list[str]:
    """Flip a 2D array diagonally"""
    return [list(row) for row in zip(*arr)]


def corners_from_arr(arr: list[str]) -> list[list[str]]:
    return [  # Top left, clockwise
        [arr[0][0], arr[0][1], arr[1][1], arr[1][0]],
        [arr[0][-2], arr[0][-1], arr[1][-1], arr[1][-2]],
        [arr[-2][-2], arr[-2][-1], arr[-1][-1], arr[-1][-2]],
        [arr[-2][0], arr[-2][1], arr[-1][1], arr[-1][0]]
    ]

def normalize_rotation(arr: list[str]) -> str:
    corners = corners_from_arr(arr)
    corner_sets = [set(c) for c in corners]
    # Two diagonally opposite corners will contain all 8 numbers
    if len(corner_sets[0] | corner_sets[2]) == 8:
        # Code is valid
        pass
    elif len(corner_sets[1] | corner_sets[3]) == 8:
        # Code is correct, but rotated 90 degrees.
        arr = rotate(arr)
        corners = corners[1:] + corners[0]
    else:
        raise Exception("No diagonally opposite corners contain all 8 colours - Invalid code")

    # We now know the top left and bottom right corners are completely different, but they could be rotated
    # The way to check a grid is correct is to check the bottom left corner
    # The top 2 pixels match the top 2 pixels of the top left corner, and the bottom 2 match the bottom right corner
    def find_valid_orientation(to_test: list[str]) -> list[str] | None:
        """Finds a valid rotation of the grid by rotating it, or None if no valid orientation exists"""
        for _ in range(4):
            current_corners = corners_from_arr(to_test)
            expected = [current_corners[0][:2], current_corners[2][2:]]
            check = [current_corners[3][:2], current_corners[3][2:]]
            if expected == check:
                return to_test
            to_test = rotate(to_test)
        return None

    valid = find_valid_orientation(arr)
    if not valid:
        # The grid could be flipped horizontally, vertically or diagonally
        methods = [flip_horizontal, flip_vertical, flip_diagonal]
        for method in methods:
            valid = find_valid_orientation(method(arr))
            if valid:
                break
    if not valid:
        raise Exception("No valid orientation found - Invalid code")
    return valid


def generate_key(arr: list[str]) -> dict[str, str]:
    """Generate a key from the corners of a normalised grid"""
    corners = corners_from_arr(arr)
    return {
        corners[0][0]: "0", corners[0][1]: "1", corners[0][2]: "2", corners[0][3]: "3",
        corners[2][2]: "4", corners[2][3]: "5", corners[2][0]: "6", corners[2][1]: "7",
    }


def check(arr: list[str]) -> bool:
    """Returns if the checksums and hashes match a normalised grid"""
    data = "".join([row[2:-2] for row in arr[2:-2]])


def decode(arr: list[str]) -> str:
    arr = normalize_rotation(arr)
    key = generate_key(arr)
    # Replace each value in the grid with the corresponding value in the key
    arr = ["".join([key[i] for i in row]) for row in arr]

    # We need to check that all the checksums and hashes match
    is_valid = check(arr)

    # The data is the whole grid, except 2 pixels on each side
    data = "".join([row[2:-2] for row in arr[2:-2]])
    # Convert each digit to a 3 bit binary number
    data = "".join([bin(int(i))[2:].zfill(3) for i in data])

    # Convert this to a byte string
    data = bytes([int(data[i:i+8], 2) for i in range(0, len(data), 8)])
    # # The original string was put through UTF-8 encoding, then base64. We need to reverse this
    return b64.b64decode(data).decode("utf8")

def main():
    test_string =   "0133407322263401 3234353465244540 2431043550340635 3415712047014306 0436241150222441 0634613546155551 7425263531144334 7545643064357062 6434054462214301 0501322565054751 3531043526364634 1421032126351762 2432265475000001 0141100665573467 5446244030667554"
    test_string = test_string.split()
    k = {0: "B", 1: "$", 2: "=", 3: "/", 4: "F", 5: "!", 6: "V", 7: "@"}
    for n in range(len(test_string)):
        test_string[n] = "".join([k[int(i)] for i in test_string[n]])
    string = rotate(test_string)

    print("".join(string))
    decoded = decode(string)
    print(decoded)

if __name__ == "__main__":
    main()
