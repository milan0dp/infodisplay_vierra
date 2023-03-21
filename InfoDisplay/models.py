import datetime
import os

from django.db import models
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


class upload_file(models.Model):
    data = models.FileField(upload_to='data/', blank=True, null=True, unique=True)
    name = models.TextField(verbose_name='name', unique=True, blank=False, null=True)
    order = models.IntegerField(verbose_name='order', null=False, blank=False, unique=False, default=0)

    def delete(self, using=None, keep_parents=False):
        if os.name == 'nt':
            os.remove(os.path.join(Path(__file__).resolve().parent.parent, self.data.name.replace('/', '\\')))
        else:
            os.remove(os.path.join(Path(__file__).resolve().parent.parent.parent, self.data.name))
        super(upload_file, self).delete()


class TV_State(models.Model):
    id = models.IntegerField(primary_key=True, blank=False)
    state = models.IntegerField(verbose_name='state', null=False, default=1)
    last_state = models.IntegerField(default=1)
    start_time = models.TimeField(default=datetime.time(6, 0, 0))
    stop_time = models.TimeField(default=datetime.time(15, 0, 0))
    r_dis_state = models.BooleanField(default=False)