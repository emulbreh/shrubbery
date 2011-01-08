TAG_SEPARATOR = ","
TAG_QUOTE_CHAR = '"'
TAG_ESCAPE_CHAR = "\\"

def quote_tag(name, force=False):
    if force or TAG_SEPARATOR in name or TAG_QUOTE_CHAR in name:
        return TAG_QUOTE_CHAR + name.replace(TAG_ESCAPE_CHAR, TAG_ESCAPE_CHAR*2).replace(TAG_QUOTE_CHAR, TAG_ESCAPE_CHAR + TAG_QUOTE_CHAR) + TAG_QUOTE_CHAR
    return name
    
def encode_tags(tags):
    return (TAG_SEPARATOR + " ").join([quote_tag(unicode(tag)) for tag in tags])

def parse_tags(tag_input):
    buf = []
    quoted = False
    i = iter(tag_input)
    def _current():
        return "".join(buf).strip()
    try:
        while True:
            c = i.next()
            if c == TAG_QUOTE_CHAR:
                if quoted:
                    tag = _current()                    
                    if tag:
                        yield tag
                    buf = []
                    quoted = False
                else:
                    quoted = True
            elif c == TAG_SEPARATOR:
                if quoted:
                    buf.append(c)
                else:
                    tag = _current()
                    if tag:
                        yield tag
                    buf = []
            elif c == TAG_ESCAPE_CHAR:
                if quoted:
                    c = i.next()
                    if not c in (TAG_ESCAPE_CHAR, TAG_QUOTE_CHAR):
                        raise ValueError("illegal escape sequence")
                buf.append(c)
            else:
                buf.append(c)                
    except StopIteration:
        if quoted:
            raise ValueError("quotes mismatch")
        tag = _current()
        if tag:
            yield tag

