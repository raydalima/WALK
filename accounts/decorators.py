from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

def student_required(view_func):
    """Decorator para views que requerem acesso de aluno"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login para acessar esta página.')
            return redirect('accounts:login')
        
        if not request.user.is_student():
            messages.error(request, 'Acesso negado. Esta área é restrita para alunos.')
            return redirect('accounts:dashboard_redirect')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def teacher_required(view_func):
    """Decorator para views que requerem acesso de professor"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login para acessar esta página.')
            return redirect('accounts:login')
        
        if not request.user.is_teacher():
            messages.error(request, 'Acesso negado. Esta área é restrita para professores.')
            return redirect('accounts:dashboard_redirect')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    """Decorator para views que requerem acesso administrativo"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login para acessar esta página.')
            return redirect('accounts:login')
        
        if not request.user.is_admin_user():
            messages.error(request, 'Acesso negado. Esta área é restrita para administradores.')
            return redirect('accounts:dashboard_redirect')
        
        return view_func(request, *args, **kwargs)
    return wrapper
