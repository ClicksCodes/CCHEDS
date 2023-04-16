

def decode(arr: list[str]) -> str:
    corners = [  # Top left, clockwise
        [arr[0][0], arr[0][1], arr[1][1], arr[1][0]],
        [arr[0][-1], arr[0][-2], arr[1][-2], arr[1][-1]],
        [arr[-1][-1], arr[-1][-2], arr[-2][-2], arr[-2][-1]],
        [arr[-1][0], arr[-1][1], arr[-2][1], arr[-2][0]],
    ]

    # 2 Diagonally opposite corners will be entirely unique.
    # One adjacent corner will include the top 2 of the top left (0 and 1)
    # And the bottom 2 of the bottom right (2 and 3)
    # The code could be rotated, and/or flipped
    # Correct for this such that the unique corners are in the top left and bottom right, and the adjacent is in the bottom left

    # Check if any of the 4 corners are unique
    for i, corner in enumerate(corners):
        if all(corner[0] != other_corner[0] for other_corner in corners[:i] + corners[i + 1 :]):
            # Rotate the list so that the unique corner is in the top left
            corners = corners[i:] + corners[:i]
            break
    else:
        # If none are unique, the top left corner must be the adjacent corner
        # Rotate the list so that the adjacent corner is in the bottom left
        corners = corners[1:] + corners[:1]

    # Check if the bottom right corner is unique
    if corners[2][0] == corners[3][0]:
        # If not, the code is flipped
        # Flip the code
        arr = [list(reversed(row)) for row in arr]

    # Convert to string
    return "\n".join("".join(row) for row in arr)

def main():
    test_string = ["01441101", "32011120", "01310432", "02047563", "21172020", "01242167", "54310654"]
    test_string = ["".join(reversed(list(s))) for s in test_string]  # Reverse
    print(decode(test_string))

if __name__ == "__main__":
    main()