from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='dashboard:index', permanent=False)),
    path('accounts/', include('apps.accounts.urls')),
    path('parametres/', include('apps.core.urls')),
    path('trades/', include('apps.trades.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('analytics/', include('apps.analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
