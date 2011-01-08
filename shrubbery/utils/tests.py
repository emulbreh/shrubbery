__test__ = {'PAGE_RANGE_TESTS':"""
>>> from shrubbery.utils.pagination import PageRanges
>>> from django.core.paginator import Paginator
>>> p = Paginator(range(30), 1)
>>> PageRanges(p.page(1), min_gap=1, before=2, after=3)
<PageRanges: [<1>; 2, 3, 4; ..; 28, 29, 30]>
>>> PageRanges(p.page(21), min_gap=1, before=2, after=3)
<PageRanges: [1, 2, 3; ..; 19, 20; <21>; 22, 23, 24; ..; 28, 29, 30]>
>>> PageRanges(p.page(21), min_gap=3, before=2, after=3)
<PageRanges: [1, 2, 3; ..; 19, 20; <21>; 22, 23, 24; ..; 28, 29, 30]>
>>> PageRanges(p.page(21), min_gap=4, before=2, after=3)
<PageRanges: [1, 2, 3; ..; 19, 20; <21>; 22, 23, 24, 25, 26, 27, 28, 29, 30]>
>>> PageRanges(p.page(30), min_gap=1, before=2, after=3, last=2)
<PageRanges: [1, 2, 3; ..; 28, 29; <30>]>
>>> PageRanges(p.page(8), min_gap=1, before=2, after=3)
<PageRanges: [1, 2, 3; ..; 6, 7; <8>; 9, 10, 11; ..; 28, 29, 30]>
>>> PageRanges(p.page(8), min_gap=2, before=2, after=3)
<PageRanges: [1, 2, 3; ..; 6, 7; <8>; 9, 10, 11; ..; 28, 29, 30]>
>>> PageRanges(p.page(8), min_gap=3, before=2, after=3)
<PageRanges: [1, 2, 3, 4, 5, 6, 7; <8>; 9, 10, 11; ..; 28, 29, 30]>
>>> PageRanges(p.page(2), min_gap=3, before=2, after=2, first=10)
<PageRanges: [1; <2>; 3, 4, 5, 6, 7, 8, 9, 10; ..; 28, 29, 30]>
>>> PageRanges(p.page(28), min_gap=3, before=2, after=2, last=10, first=10)
<PageRanges: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10; ..; 21, 22, 23, 24, 25, 26, 27; <28>; 29, 30]>
>>> PageRanges(p.page(15), before=20, after=20)
<PageRanges: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14; <15>; 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]>
>>> PageRanges(p.page(15), first=20, last=20)
<PageRanges: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14; <15>; 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]>
"""}