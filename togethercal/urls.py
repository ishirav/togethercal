"""togethercal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth import views as auth_views

from togethercal.main import views

urlpatterns = [
    url(r'^day/$', views.day_view, name="day"),
    url(r'^add/$', views.add_view, name="add"),
    url(r'^form/(O|S|W)/$', views.form_view, name="form"),
    url(r'^edit/(\d+)/$', views.edit_view, name="edit"),
    url(r'^$', views.main_view, name="main"),
    url(r'^month/$', views.month_view, name="month"),
    url(r'^ical/$', views.ical_view, name="ical"),
    url(r'^mail/inbound/$', views.inbound_mail_view, name="inbound_mail"),
    url(r'^login/$', auth_views.login, {'template_name': 'login.html'}, name="login"),
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
