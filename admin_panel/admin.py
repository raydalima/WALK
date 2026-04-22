from django.contrib import admin

from .models import (
    AdministrativeProfile,
    CalendarEvent,
    EmailCommunication,
    EmailCommunicationRecipient,
    EmailTemplate,
    PanelNotice,
)


@admin.register(AdministrativeProfile)
class AdministrativeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')


class EmailCommunicationRecipientInline(admin.TabularInline):
    model = EmailCommunicationRecipient
    extra = 0
    readonly_fields = (
        'email',
        'name',
        'recipient_type',
        'student',
        'teacher',
        'status',
        'processed_at',
        'error_message',
    )
    can_delete = False


@admin.register(EmailCommunication)
class EmailCommunicationAdmin(admin.ModelAdmin):
    list_display = (
        'subject',
        'category',
        'send_type',
        'recipient_group',
        'sent_by',
        'scheduled_at',
        'sent_at',
        'status',
        'successful_recipients',
        'failed_recipients',
    )
    list_filter = ('category', 'send_type', 'recipient_group', 'status', 'sent_at', 'scheduled_at')
    search_fields = ('subject', 'message', 'sent_by__email')
    readonly_fields = (
        'sent_by',
        'created_at',
        'sent_at',
        'status',
        'total_recipients',
        'successful_recipients',
        'failed_recipients',
        'error_message',
    )
    inlines = [EmailCommunicationRecipientInline]


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_by', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'default_subject', 'default_body')


@admin.register(PanelNotice)
class PanelNoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'audience', 'turma', 'is_featured', 'is_visible', 'published_at')
    list_filter = ('category', 'audience', 'is_featured', 'is_visible')
    search_fields = ('title', 'summary', 'content')


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'starts_at', 'audience', 'turma', 'is_visible')
    list_filter = ('event_type', 'audience', 'is_visible', 'is_featured')
    search_fields = ('title', 'description', 'location')
