
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('enter/', views.enter_record, name='enter'),
    path('export/', views.export_excel, name='export'),
    path('export_excel/', views.export_excel, name='export_excel'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit/<int:record_id>/', views.edit_record, name='edit_record'),
    path('delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('inline_update/', views.inline_update, name='inline_update'),

]

