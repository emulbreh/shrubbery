import re


_camel_case_re = re.compile('_([a-z])')
def camel_case(s, initial_cap=None):
    s = _camel_case_re.sub(lambda m: m.group(1).upper(), s)
    if initial_cap is not None:
        if initial_cap:
            s = s[0].upper() + s[1:]
        else:
            s = s[0].lower() + s[1:]
    return s


_camel_split_re = re.compile(r'[A-Z0-9]+(?![a-z])|\w[^A-Z]+')
def camel_split(s):
    return [m.group(0) for m in _camel_split_re.finditer(s)]

