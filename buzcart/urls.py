
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from auths.views import CustomTokenObtainPairView
urlpatterns = [
        path('api/docs/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
        path('api/auths/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auths/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('api/auths/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        path('admin/', admin.site.urls),
        path('api/common/', include('common.urls')),
        path('api/auths/', include('auths.urls')),
        path('api/verification/', include('verification.urls')),
        path('api/feed/', include('feed.urls')),
        path('api/commerce/', include('commerce.urls')),
        path('api/notifications/', include('notifications.urls')),
        path('api/analytics/', include('analytics.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
