# ===================================================================
# Projeto: Inventory Management
# Autor: Henrique José Dias Pereira
# Data: 06/11/2024
# Direitos Autorais: © 2024 Henrique José Dias Pereira. Todos os direitos reservados.
# ===================================================================

from django.contrib import admin
from django.urls import path
from .views import Index, SignUpView, Dashboard, AddItem, EditItem, DeleteItem, ItemFilter, MostSoldItemsReport, MovementLogView, DecreaseItemView, IncreaseItemView, ClearLogsView
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

urlpatterns = [
    path('', Index.as_view(), name = 'index'),
    path('item-filter/', ItemFilter.as_view(), name = 'item-filter'),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('clear-logs/', ClearLogsView.as_view(), name='clear-logs'),
    path('add-item/', AddItem.as_view(), name = 'add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name = 'edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name = 'delete-item'),
    path('signup/', SignUpView.as_view(), name ='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name = 'login'),
    path('logout/', auth_views.LogoutView.as_view(template_name = 'inventory/logout.html'), name= 'logout'),
    path('handle_message/', views.handle_message, name='handle_message'),
    path('update_intents/', views.update_intents_file, name='update_intents_file'),
    path('chat/', views.chat, name='chat'),
    path('report/most_sold/', MostSoldItemsReport.as_view(), name='most_sold_items_report'),
    path('movement_log/', MovementLogView.as_view(), name='movement_log'),
    path('decrease/<int:pk>', DecreaseItemView.as_view(), name='decrease-item'),
    path('increase/<int:pk>', IncreaseItemView.as_view(), name='increase-item'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)