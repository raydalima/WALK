from django.contrib import admin

from .models import Activity, ActivityResult, Answer, Choice, EssaySubmission, Question, Quiz, Submission


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'quiz', 'type', 'order', 'points')
    list_filter = ('type',)
    search_fields = ('text',)
    inlines = [ChoiceInline]


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'is_published', 'created_at')
    list_filter = ('is_published', 'course')
    search_fields = ('title',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'quiz',
        'student',
        'attempt',
        'status',
        'submitted_at',
    )
    list_filter = ('status', 'quiz')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'submission',
        'question',
        'auto_score',
        'teacher_score',
    )


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'turma', 'course', 'status', 'due_date')
    list_filter = ('status', 'turma', 'course')
    search_fields = ('title', 'description')


@admin.register(ActivityResult)
class ActivityResultAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity', 'student', 'status', 'submitted_at', 'corrected_at')
    list_filter = ('status', 'activity')
    search_fields = ('activity__title', 'student__user__first_name', 'student__user__last_name', 'submission_url')


@admin.register(EssaySubmission)
class EssaySubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'student', 'course', 'status', 'submitted_at', 'corrected_at')
    list_filter = ('status', 'course')
    search_fields = ('title', 'student__user__first_name', 'student__user__last_name', 'submission_url')
