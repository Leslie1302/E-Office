from django.views.generic import ListView, CreateView, UpdateView, View
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
from django.db.models import Q
from .models import Task, Reminder
from .forms import TaskForm, SignUpForm
from django.contrib.auth.models import User
from .tasks import send_task_assignment_notification
from django.utils import timezone

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

        # Calculate countdown for each task
        now = timezone.now()
        for task in context['tasks']:
            if task.deadline:
                time_left = task.deadline - now
                task.countdown = {
                    'days': time_left.days,
                    'hours': time_left.seconds // 3600,
                    'is_overdue': time_left.total_seconds() < 0
                }
            else:
                task.countdown = None

        # Get officers with overdue tasks
        overdue_tasks = Task.objects.filter(
            is_archived=False,
            deadline__lt=now,
            status__in=['dispatched-officer', 'draft', 'finalized-draft']
        ).select_related('assignee')
        
        overdue_officers = {}
        for task in overdue_tasks:
            officer = task.assignee
            if officer not in overdue_officers:
                overdue_officers[officer] = []
            overdue_officers[officer].append(task)
        
        context['overdue_officers'] = [
            {
                'officer': officer,
                'tasks': tasks,
                'reminder_url': reverse_lazy('send_reminder', kwargs={'user_id': officer.id})
            }
            for officer, tasks in overdue_officers.items()
        ]
        
        return context

class EmployeeDashboardView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/employee_dashboard.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        queryset = Task.objects.filter(assignee=self.request.user, is_archived=False)
        
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
        
        # Add reminders for overdue tasks
        now = timezone.now()
        reminders = Reminder.objects.filter(
            user=self.request.user,
            is_active=True,
            is_dismissed=False,
            tasks__is_archived=False,
            tasks__deadline__lt=now,
            tasks__status__in=['dispatched-officer', 'draft', 'finalized-draft']
        ).distinct()
        
        context['reminders'] = [
            {
                'id': reminder.id,
                'created_by': reminder.created_by.username,
                'tasks': reminder.tasks.all(),
                'created_at': reminder.created_at,
                'message': reminder.message
            }
            for reminder in reminders
        ]
        
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
        send_task_assignment_notification(form.instance.id, form.instance.assignee.id)
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
        if not (request.user == task.assignee or request.user.is_superuser or (hasattr(request.user, 'profile') and user.profile.is_manager)):
            messages.error(request, "You are not authorized to update this task.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        original_task = Task.objects.get(id=form.instance.id)
        response = super().form_valid(form)
        if original_task.assignee != form.instance.assignee:
            send_task_assignment_notification(form.instance.id, form.instance.assignee.id)
        messages.success(self.request, "Task updated successfully.")
        return response

class TaskStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['status']
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task_list')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager):
            return Task.objects.all()
        return Task.objects.filter(assignee=user)

    def dispatch(self, request, *args, **kwargs):
        task = self.get_object()
        if not (request.user == task.assignee or request.user.is_superuser or (hasattr(request.user, 'profile') and user.profile.is_manager)):
            messages.error(request, "You are not authorized to update this task.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Task status updated to {form.instance.status}.")
        
        # Deactivate reminders if task is completed
        if form.instance.status == 'signed-dispatched':
            Reminder.objects.filter(tasks=form.instance, user=self.request.user, is_active=True).update(is_active=False)
        
        return response

class TaskDirectStatusUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk, status):
        user = request.user
        status_map = {
            'dispatched-officer': 'dispatched-officer',
            'draft': 'draft',
            'finalized-draft': 'finalized-draft',
            'signed-dispatched': 'signed-dispatched',
        }
        try:
            task = Task.objects.get(pk=pk)
            if not (user == task.assignee or user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
                messages.error(request, "You are not authorized to update this task.")
                return redirect('employee_dashboard')
            
            if status in status_map:
                task.status = status_map[status]
                task.save()
                messages.success(request, f"Task status updated to {task.get_status_display()}.")
                
                # Deactivate reminders if task is completed
                if task.status == 'signed-dispatched':
                    Reminder.objects.filter(tasks=task, user=task.assignee, is_active=True).update(is_active=False)
            else:
                messages.error(request, "Invalid status.")
                
        except Task.DoesNotExist:
            messages.error(request, "Task does not exist.")
            
        return redirect('employee_dashboard' if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)) else 'manager_dashboard')

class SendReminderView(LoginRequiredMixin, View):
    def get(self, request, user_id):
        user = request.user
        if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            messages.error(request, "Only managers can send reminders.")
            return redirect('manager_dashboard')
        
        try:
            assignee = User.objects.get(id=user_id)
            overdue_tasks = Task.objects.filter(
                assignee=assignee,
                is_archived=False,
                deadline__lt=timezone.now(),
                status__in=['dispatched-officer', 'draft', 'finalized-draft']
            )
            
            return render(request, 'tasks/send_reminder.html', {
                'assignee': assignee,
                'overdue_tasks': overdue_tasks,
            })
                
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            return redirect('manager_dashboard')

    def post(self, request, user_id):
        user = request.user
        if not (user.is_superuser or (hasattr(user, 'profile') and user.profile.is_manager)):
            messages.error(request, "Only managers can send reminders.")
            return redirect('manager_dashboard')
        
        try:
            assignee = User.objects.get(id=user_id)
            task_ids = request.POST.getlist('tasks')
            message = request.POST.get('message')
            
            overdue_tasks = Task.objects.filter(
                id__in=task_ids,
                assignee=assignee,
                is_archived=False,
                deadline__lt=timezone.now(),
                status__in=['dispatched-officer', 'draft', 'finalized-draft']
            )
            
            if overdue_tasks.exists():
                reminder = Reminder.objects.create(
                    user=assignee,
                    created_by=user,
                    is_active=True,
                    message=message
                )
                reminder.tasks.set(overdue_tasks)
                messages.success(request, f"Reminder sent to {assignee.username}.")
            else:
                messages.info(request, f"No valid overdue tasks selected for {assignee.username}.")
                
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
            
        return redirect('manager_dashboard')

class DismissReminderView(LoginRequiredMixin, View):
    def post(self, request, reminder_id):
        try:
            reminder = Reminder.objects.get(id=reminder_id, user=request.user)
            reminder.is_dismissed = True
            reminder.save()
            messages.success(request, "Reminder dismissed.")
        except Reminder.DoesNotExist:
            messages.error(request, "Reminder does not exist.")
        return redirect('employee_dashboard')

class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'tasks/signup.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Account created successfully. Please log in.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Error creating account. Please check the form.")
        return super().form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect('task_list')
        return super().dispatch(request, *args, **kwargs)