from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Language, Translation


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'translation_count')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    
    def translation_count(self, obj):
        return obj.translations.count()
    translation_count.short_description = _('Translations')


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ('truncated_message_id', 'language', 'truncated_translation', 'context', 'location', 'updated_at')
    list_filter = ('language', 'context')
    search_fields = ('message_id', 'translation', 'context', 'location')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('language', 'message_id', 'translation')
        }),
        (_('Additional Information'), {
            'fields': ('context', 'location', 'created_at', 'updated_at')
        }),
    )
    
    def truncated_message_id(self, obj):
        return (obj.message_id[:50] + '...') if len(obj.message_id) > 50 else obj.message_id
    truncated_message_id.short_description = _('Message ID')
    
    def truncated_translation(self, obj):
        if not obj.translation:
            return format_html('<span style="color: #FF0000;">Not translated</span>')
        return (obj.translation[:50] + '...') if len(obj.translation) > 50 else obj.translation
    truncated_translation.short_description = _('Translation')
