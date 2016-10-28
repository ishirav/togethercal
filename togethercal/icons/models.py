# -*- coding: utf-8 -*-
from django.db import models

import os
import random


class Icon(models.Model):

    image = models.ImageField(upload_to='icons')
    name  = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = u'אייקון'
        verbose_name_plural = u'אייקונים'

    def __unicode__(self):
        return self.name or self.image.name

    def clean(self):
        if self.image and not self.name:
            self.name = os.path.basename(os.path.splitext(self.image.name)[0])

    def keywords(self):
        return ', '.join(self.iconkeyword_set.values_list('keyword', flat=True))


class IconKeyword(models.Model):

    icon    = models.ForeignKey(Icon)
    keyword = models.CharField(max_length=50)

    def __unicode__(self):
        return self.keyword


def icon_for_text(text):
    candidates = set()
    words = text.split()
    # look for word pairs
    pairs = zip(words[:-1], words[1:])
    for pair in pairs:
        candidates.update(Icon.objects.filter(iconkeyword__keyword__iexact=' '.join(pair)))
    # look for single words
    if not candidates:
        for word in words:
            candidates.update(Icon.objects.filter(iconkeyword__keyword__iexact=word))
    return random.choice(list(candidates)) if candidates else None
