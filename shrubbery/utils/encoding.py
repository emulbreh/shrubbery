
def base_encode(x, chars='0123456789'):
    b = len(chars)
    buf = []
    n = x
    while n:
        n, i = divmod(n, b)
        buf.append(chars[i])
    return ''.join(buf)

def base36_encode(x):
    return base_encode(x, chars='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')
