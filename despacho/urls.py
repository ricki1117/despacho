from django.urls import path
from despacho.views import login_view, crear_cliente,crear_caso, vista_tablas,gestion_usuarios  # Import the view
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', login_view, name='login'),
    path('crear_cliente/', crear_cliente, name='gestion_cliente'),

    path('crear_caso/', crear_caso, name='crear_caso'),

    path('vista_tablas/', vista_tablas, name='vista_tablas'),
    path('gestion_usuarios/', gestion_usuarios, name='gestion_usuarios'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

]