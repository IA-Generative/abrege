import numpy as np

A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])

P = np.array([1, 1, 1])


def main():
    print(np.sum(P / A, axis=1))


if __name__ == "__main__":
    main()
