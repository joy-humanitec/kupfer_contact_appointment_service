from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health_check/', include('health_check.urls')),
    path(r'api/', include('crm.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
