from sign_magnitude import sign_magnitude

def ones_complement(num: int):

    if num >= 0:
        sign_magnitude(num)

    else:
        bit_array = sign_magnitude(num)
        for i in bit_array[1:]:
            if i == 0:
                i = 1
            
            else:
                i = 0