# -*- coding: utf-8 -*-

class PageRange(object):
    def __init__(self, start, stop, ellipsis=False, current=False):
        self.range = xrange(start, stop)
        self.ellipsis = ellipsis
        self.current = current
        
    def __len__(self):
        return len(self.range)
        
    def __iter__(self):
        return iter(self.range)
        
    def __unicode__(self):
        if self.ellipsis:
            return u"…"
        return repr(self)
        
    def __repr__(self):
        if self.ellipsis:
            # use only two dots; doctests don't like three
            return ".."
        elif self.current:
            return "<%s>" % self.range[0]
        else:
            return ", ".join([str(num) for num in self.range])
        
class PageRanges(object):
    def __init__(self, page, first=3, last=3, before=5, after=5, min_gap=1):
        self.page = page
        self.first, self.last = first, last
        self.before, self.after = before, after
        self.min_gap = min_gap
        
    def __repr__(self):
        return "<PageRanges: [%s]>" % "; ".join(map(repr, self))
        
    def __iter__(self):
        count = self.page.paginator.count
        n = len(self.page.paginator.page_range)
        p = self.page.number
        
        if p != 1:
            before = max(self.before, self.last - n + p - 1)
            if p <= self.first + before + self.min_gap:
                yield PageRange(1, p)
            else:
                e_start = self.first + 1
                e_stop = p - before
                yield PageRange(1, e_start)
                yield PageRange(e_start, e_stop, ellipsis=True)
                yield PageRange(e_stop, p)
        
        yield PageRange(p, p + 1, current=True)

        if p != n:
            after = max(self.after, self.first - p)
            if p > n - self.last - after - self.min_gap:
                yield PageRange(p + 1, n + 1)
            else:
                e_start = p + 1 + after
                e_stop = n - self.last + 1
                yield PageRange(p + 1, e_start)
                yield PageRange(e_start, e_stop, ellipsis=True)
                yield PageRange(e_stop, n + 1)
        
