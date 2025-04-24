from django.db import models
from django.utils import timezone


class Language(models.Model):
    """
    Model for storing available languages for translation.
    """
    code = models.CharField(max_length=10, unique=True, help_text="Language code (e.g., 'en', 'es-mx')")
    name = models.CharField(max_length=50, help_text="Human-readable language name")
    is_active = models.BooleanField(default=True, help_text="Whether this language is active for translation")
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Translation(models.Model):
    """
    Model for storing translations for various languages.
    """
    language = models.ForeignKey(
        Language, 
        on_delete=models.CASCADE, 
        related_name='translations'
    )
    message_id = models.TextField(help_text="Original untranslated string")
    context = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="Context for ambiguous strings"
    )
    translation = models.TextField(
        blank=True, 
        help_text="Translated string"
    )
    location = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="File location where this string was found"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('language', 'message_id', 'context')
        ordering = ['language', 'message_id']
        verbose_name = 'Translation'
        verbose_name_plural = 'Translations'
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['language', 'message_id']),
        ]
    
    def __str__(self):
        return f"{self.message_id[:30]}... ({self.language.code})"
