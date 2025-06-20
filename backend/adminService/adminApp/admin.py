from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import User, Model, EmbeddingModel, ModelConfiguration, Category, Chat, Message, SystemPrompt

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Настройки чата', {'fields': ('system_prompt',)}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(Model)
class ModelAdmin(ModelAdmin):
    list_display = ('name', 'temperature')
    search_fields = ('name',)

@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(ModelConfiguration)
class ModelConfigurationAdmin(ModelAdmin):
    list_display = ('name', 'llm_model', 'embedding_model', 'is_active', 'created_at')
    list_filter = ('is_active', 'llm_model', 'embedding_model')
    search_fields = ('name',)
    date_hierarchy = 'created_at'

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('parent',)
    search_fields = ('name',)

@admin.register(Chat)
class ChatAdmin(ModelAdmin):
    list_display = ('title', 'user', 'is_active', 'created_at')
    list_filter = ('is_active', 'user')
    search_fields = ('title', 'user__username')
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ('chat', 'role', 'request_type', 'created_at', 'configuration', 'rating')
    list_filter = ('role', 'request_type', 'configuration', 'category_level_1', 'category_level_2')
    search_fields = ('content', 'chat__title', 'request_type')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(SystemPrompt)
class SystemPromptAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'text')
    fieldsets = (
        (None, {
            'fields': ('name', 'text')
        }),
    )
