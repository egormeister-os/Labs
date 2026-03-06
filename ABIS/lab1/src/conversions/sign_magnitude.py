def sign_magnitude(num: int) -> list[int]: 
    bit_array = [0] * 32

    if num < 0:
        bit_array[0] = 1
        num = abs(num)

    i = 1
    while num > 0:
        bit = num % 2
        num = num // 2
        bit_array[-i] = bit
        i += 1

    return bit_array
