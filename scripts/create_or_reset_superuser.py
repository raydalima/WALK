# Cria ou reseta um superusuário para acesso local ao Django Admin.
# Uso (na raiz do projeto):
#   python3 manage.py shell < scripts/create_or_reset_superuser.py

from django.contrib.auth import get_user_model

USERNAME = "swep@admin.com"
EMAIL = "swep@admin.com"
PASSWORD = "Swep2026#"

User = get_user_model()

user = (
    User.objects.filter(username=USERNAME).first()
    or User.objects.filter(email=EMAIL).first()
)

if user is None:
    user = User.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
    )
else:
    user.username = USERNAME
    if getattr(user, "email", None) is not None:
        user.email = EMAIL
    user.set_password(PASSWORD)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.save()

print(f"OK: superuser ready -> {USERNAME} (id={user.pk})")
