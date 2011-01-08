from unittest import TestCase
import datetime

from django.db import models

from shrubbery.db.utils import MappedQ

class Dt(models.Model):
    d = models.DateField()
    dt = models.DateTimeField()
    
    class Meta:
        app_label = "db"
        
class DateQ(MappedQ):
    sql_template = "DATE(%s) = %%s"

class QUtilsTest(TestCase):
    def test(self):
        stamp = datetime.datetime.now()
        for i in range(7):
            dt = stamp + datetime.timedelta(days=i)
            Dt.objects.create(d=dt.date(), dt=dt)
            Dt.objects.create(d=dt.date(), dt=stamp)
        #print Dt.objects.complex_filter(DateQ(d=models.F('d')))
        
        
        