import numba
import numpy as np

@numba.njit
def checksum_11b(data: bytes):
    arr = np.frombuffer(data, dtype=np.uint8)
    total = 0
    for byte in arr:
        total += byte
    while total > 0xFFFF:
        total = (total & 0xFFFF)
    return total


