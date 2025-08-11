"""
URL configuration for arvion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from core.views import HomeView, AboutView, switch_language

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("switch-language/", switch_language, name="switch_language"),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('blog/', include('blog.urls', namespace='blog')),
    path('projects/', include('portfolio.urls', namespace='portfolio')),
    path('services/', include('services.urls', namespace='services')),
    path('contact/', include('leads.urls', namespace='leads')),
    prefix_default_language=False,  # ← این خط مهمه
)