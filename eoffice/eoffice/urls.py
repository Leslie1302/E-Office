from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tasks/', include('tasks.urls')),
    path('', RedirectView.as_view(url=reverse_lazy('task_list')), name='root'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)