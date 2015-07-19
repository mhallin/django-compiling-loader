from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='benchmark/main.html')),
    url(r'^layout$',
        TemplateView.as_view(template_name='benchmark/layout.html')),
    url(r'^loop$', views.LoopView.as_view()),
)
