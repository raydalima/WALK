from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm
from .models import User
from django.utils.http import url_has_allowed_host_and_scheme


def _authenticate_user_by_input(request, username_input, password):
    """Tenta autenticar pelo username/email fornecido no formulário.

    Primeiro tenta autenticar diretamente com o valor informado. Se falhar
    e o valor parecer um email (contém '@'), tenta buscar o usuário pelo
    email e autenticar usando o USERNAME_FIELD do modelo.
    """
    user = authenticate(request, username=username_input, password=password)

    if user is None and '@' in (username_input or ''):
        try:
            u_obj = User.objects.filter(email=username_input).first()
            if u_obj:
                if hasattr(u_obj, 'USERNAME_FIELD'):
                    username_for_auth = getattr(
                        u_obj,
                        u_obj.USERNAME_FIELD,
                        None,
                    )
                else:
                    username_for_auth = getattr(u_obj, 'username', None)

                if not username_for_auth:
                    username_for_auth = u_obj.email

                user = authenticate(
                    request,
                    username=username_for_auth,
                    password=password,
                )
        except Exception:
            user = None

    return user


def login_view(request):
    """View para login de usuários com suporte a 'email' ou 'username'."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        username_input = (
            request.POST.get('username') or request.POST.get('email') or ''
        )
        password = request.POST.get('password', '')

        user = _authenticate_user_by_input(
            request, username_input, password
        )

        if user is not None:
            login(request, user)
            welcome_msg = f'Bem-vindo(a), {user.get_full_name()}!'
            messages.success(request, welcome_msg)

            if next_url:
                # redirecionar para caminhos relativos
                if next_url.startswith('/'):
                    return redirect(next_url)

                host = request.get_host()
                if url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={host},
                ):
                    return redirect(next_url)

            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, 'E-mail, nome de usuário ou senha inválidos.')

    form = CustomLoginForm()
    return render(
        request,
        'accounts/login.html',
        {'form': form, 'next': next_url},
    )


@login_required
def logout_view(request):
    """View para logout"""
    logout(request)
    messages.success(request, 'Saída realizada com sucesso!')
    return redirect('accounts:login')


@login_required
def dashboard_redirect(request):
    """Redireciona o usuário para o dashboard apropriado baseado no tipo."""
    user = request.user

    try:
        if user.is_admin_user():
            return redirect('/painel/')
    except Exception:
        pass

    try:
        if user.is_teacher():
            return redirect('/professor/')
    except Exception:
        pass

    try:
        if user.is_student():
            return redirect('/aluno/')
    except Exception:
        pass

    messages.error(request, 'Tipo de usuário inválido.')
    return redirect('accounts:login')


def home(request):
    """View da página inicial."""
    return render(request, 'index.html', {})


@login_required
def profile(request):
    """Página de perfil do usuário."""
    return render(request, 'accounts/profile.html')


def login_student_page(request):
    """Login específico para alunos; redireciona para /aluno/ após sucesso."""
    next_url = '/aluno/'

    if request.method == 'POST':
        username_input = (
            request.POST.get('username') or request.POST.get('email') or ''
        )
        password = request.POST.get('password', '')

        user = _authenticate_user_by_input(
            request, username_input, password
        )

        if user is not None:
            login(request, user)
            welcome_msg = f'Bem-vindo(a), {user.get_full_name()}!'
            messages.success(request, welcome_msg)
            return redirect(next_url)
        else:
            messages.error(request, 'E-mail, nome de usuário ou senha inválidos.')

    form = CustomLoginForm()
    return render(
        request,
        'accounts/login_student.html',
        {'form': form, 'next': next_url, 'role': 'Aluno'},
    )


def login_teacher_page(request):
    form = CustomLoginForm()
    return render(
        request,
        'accounts/login_teacher.html',
        {'form': form, 'next': '/professor/', 'role': 'Professor'},
    )


def login_gestao_page(request):
    """Login para painel de gestão; só permite contas administrativas."""
    next_url = '/painel/'

    if request.method == 'POST':
        username_input = (
            request.POST.get('username') or request.POST.get('email') or ''
        )
        password = request.POST.get('password', '')

        user = _authenticate_user_by_input(
            request, username_input, password
        )

        if user is not None:
            is_admin = False
            try:
                if hasattr(user, 'is_admin_user'):
                    is_admin = user.is_admin_user()
                else:
                    is_admin = False
            except Exception:
                is_admin = False

            if not is_admin:
                is_admin = (
                    getattr(user, 'is_staff', False)
                    or getattr(user, 'is_superuser', False)
                )

            if is_admin:
                login(request, user)
                welcome_msg = f'Bem-vindo(a), {user.get_full_name()}!'
                messages.success(request, welcome_msg)
                return redirect(next_url)
            else:
                err = (
                    'A conta não possui permissão para acessar o painel '
                    'administrativo.'
                )
                messages.error(request, err)
        else:
            messages.error(request, 'E-mail, nome de usuário ou senha inválidos.')

    form = CustomLoginForm()
    return render(
        request,
        'accounts/login_gestao.html',
        {'form': form, 'next': next_url, 'role': 'Administrativo'},
    )
