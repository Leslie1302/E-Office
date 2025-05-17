from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('employee/dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('archived/dashboard/', views.ArchivedDashboardView.as_view(), name='archived_dashboard'),
    path('task/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('task/update/<int:pk>/', views.TaskUpdateView.as_view(), name='task_update'),
    path('task/status/<int:pk>/', views.TaskStatusUpdateView.as_view(), name='task_status_update'),
    path('task/status-update/<int:pk>/<str:status>/', views.TaskDirectStatusUpdateView.as_view(), name='task_direct_status_update'),
    path('send-reminder/<int:user_id>/', views.SendReminderView.as_view(), name='send_reminder'),
]