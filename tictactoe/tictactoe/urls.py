from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path(f'{settings.ADMIN_URL}', admin.site.urls),

    # Apps
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('games/', include('apps.frontend.urls', namespace='frontend')),
    path('', include('apps.core.urls', namespace='core')),

    # API routes
    path('api/', include('apps.api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)