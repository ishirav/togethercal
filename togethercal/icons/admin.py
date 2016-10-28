from django.contrib import admin

from models import *


class IconKeywordInline(admin.TabularInline):

    model = IconKeyword


class IconAdmin(admin.ModelAdmin):

    list_display = ('name', 'keywords')
    inlines = [IconKeywordInline]


admin.site.register(Icon, IconAdmin)
