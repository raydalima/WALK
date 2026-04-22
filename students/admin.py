from django.contrib import admin
from .models import Student, PreRegistration

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'enrollment_number', 'cpf', 'is_active', 'enrollment_date']
    list_filter = ['is_active', 'enrollment_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'enrollment_number', 'cpf']
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Dados Pessoais', {
            'fields': ('birth_date', 'cpf', 'rg')
        }),
        ('Endereço', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Informações Acadêmicas', {
            'fields': ('enrollment_number',)
        }),
        ('Contato de Emergência', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
        ('Situação', {
            'fields': ('is_active', 'notes')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nome Completo'


def _get_fields_for_model(model, preferred):
    try:
        model_fields = [f.name for f in model._meta.fields]
        return tuple(f for f in preferred if f in model_fields)
    except Exception:
        return ()


@admin.register(PreRegistration)
class PreRegistrationAdmin(admin.ModelAdmin):
    list_display = _get_fields_for_model(PreRegistration, ['id', 'name', 'email', 'phone', 'is_reviewed', 'created_at']) or ('__str__',)
    search_fields = _get_fields_for_model(PreRegistration, ['name', 'email', 'cpf', 'phone'])
    list_filter = _get_fields_for_model(PreRegistration, ['gender', 'state', 'has_device', 'is_reviewed'])
    readonly_fields = _get_fields_for_model(PreRegistration, ['created_at', 'reviewed_at'])
