from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include, reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm


urlpatterns = [
    path('pages/', include('pages.urls', namespace='pages')),
    path('admin/', admin.site.urls),
    # Добавлен GET из-за запроса в шаблоне header. Шаблоны менять нельзя
    path('auth/logout/',
         LogoutView.as_view(
             template_name='registration/logged_out.html',
             next_page='blog:index',
             http_method_names=['get', 'post']
         ),
         name='logout'),
    path('auth/', include('django.contrib.auth.urls')),
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('pages:homepage'),
        ),
        name='registration',
    ),
    path('', include('blog.urls', namespace='blog')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
