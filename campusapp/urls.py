from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('attendance/', views.attendance_calculator, name='attendance'),
    path('marks/', views.marks_calculator, name='marks'),
    path('help/', views.help_page, name='help'),
    path('grade/', views.grade_calculator, name='grade'),
]