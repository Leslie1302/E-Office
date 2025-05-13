from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Task
from .forms import TaskForm
from django.utils import timezone
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.is_staff:  # Manager role
        tasks = Task.objects.all()
        return render(request, 'manager_dashboard.html', {'tasks': tasks})
    else:  # Employee role
        tasks = Task.objects.filter(assignee=request.user)
        return render(request, 'employee_dashboard.html', {'tasks': tasks})

@login_required
def create_task(request):
    if not request.user.is_staff:
        messages.error(request, "Only managers can create tasks.")
        return redirect('dashboard')
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, "Task created successfully.")
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'task_form.html', {'form': form})

@login_required
def update_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user != task.assignee:
        messages.error(request, "You are not authorized to update this task.")
        return redirect('dashboard')
    if request.method == 'POST':
        progress = request.POST.get('progress')
        status = request.POST.get('status')
        if progress:
            task.progress = int(progress)
        if status:
            task.status = status
            if status == 'completed':
                task.progress = 100
        task.save()
        messages.success(request, "Task updated successfully.")
        return redirect('dashboard')
    return render(request, 'employee_dashboard.html', {'tasks': Task.objects.filter(assignee=request.user)})

@login_required
def logout_view(request):
    logout(request)  # Log out the user
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')  # Redirect to login page