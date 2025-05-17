from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q
from .models import Task
from .forms import TaskForm
from django.contrib.auth.models import User  # Added import

class CustomLoginView(LoginView):
    template_name = 'tasks/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('task_list')

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager):
                return reverse_lazy('manager_dashboard')
            return reverse_lazy('employee_dashboard')
        return super().get_success_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "You have logged in successfully.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)

class CustomLogoutView(LogoutView):
    template_name = 'tasks/logout.html'
    next_page = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        messages.success(request, "You have been logged out successfully.")
        return super().dispatch(request, *args, **kwargs)

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(is_archived=False)
        if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            queryset = queryset.filter(assignee=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        assignee = self.request.GET.get('assignee')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if assignee and (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            queryset = queryset.filter(assignee__username=assignee)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        context['assignees'] = User.objects.all() if (self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.is_manager)) else []
        return context

class ManagerDashboardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/manager_dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            messages.error(self.request, "Only managers can access the manager dashboard.")
            return Task.objects.none()
        
        queryset = Task.objects.filter(is_archived=False)
        
        # Apply filters
        status = self.request.GET.get('status')
        assignee = self.request.GET.get('assignee')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if assignee:
            queryset = queryset.filter(assignee__username=assignee)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        context['assignees'] = User.objects.all()
        return context

class EmployeeDashboardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/employee_dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(assignee=self.request.user, is_archived=False)
        
        # Apply filters
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        return context

class ArchivedDashboardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/archived_dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.filter(is_archived=True)
        if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            queryset = queryset.filter(assignee=user)
        
        # Apply filters
        status = self.request.GET.get('status')
        assignee = self.request.GET.get('assignee')
        search = self.request.GET.get('search')
        
        if status:
            queryset = queryset.filter(status=status)
        if assignee and (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            queryset = queryset.filter(assignee__username=assignee)
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        context['assignees'] = User.objects.all() if (self.request.user.is_superuser or (hasattr(self.request.user, 'profile') and self.request.user.profile.is_manager)) else []
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_manager)):
            messages.error(request, "Only managers can create tasks.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Task created successfully.")
        return response

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager):
            return Task.objects.all()
        return Task.objects.filter(assignee=user)

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if not (request.user == task.assignee or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_manager)):
            messages.error(request, "You are not authorized to update this task.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Task updated successfully.")
        return response

class TaskStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['status']
    template_name = 'tasks/task_form.html'  # Not used, as we redirect
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager):
            return Task.objects.all()
        return Task.objects.filter(assignee=user)

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if not (request.user == task.assignee or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_manager)):
            messages.error(self.request, "You are not authorized to update this task.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Task status updated to {form.instance.status}.")
        return response