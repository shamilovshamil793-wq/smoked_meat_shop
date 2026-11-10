from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
]

# В DEBUG отдаём медиа и статику самим Django
# В dev-режиме Django сам отдаёт статику и медиа.
# В production этим занимается nginx (см. STATIC_ROOT и MEDIA_ROOT
# в settings.py — туда собираются файлы через collectstatic).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
