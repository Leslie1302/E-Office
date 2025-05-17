from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('employee/dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('archived/', views.ArchivedDashboardView.as_view(), name='archived_dashboard'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('task/new/', views.TaskCreateView.as_view(), name='task_create'),
    path('task/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_update'),
    path('task/<int:pk>/status/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),
]