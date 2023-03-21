"""infodisplay_vierra URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from InfoDisplay.views import *
from infodisplay_vierra import settings

urlpatterns = [
                  path('up', file_upload),
                  path('cr', check_re), #Überprüft ob Bilddaten oder einstellungen Geändert wurden
                  path('ct/<int:time>', change_sw_time), # Ändern der Umschaltzeit
                  path('tv/<int:in_State>', tv), #
                  path('', home),
                  path('rm/<str:file>', file_remove),
                  path('upd/<str:file>/<str:order>', file_order_update),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
