from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Translation, Language
from .translation import db_translation
from .constants import TRANSLATION_CACHE_KEY_PREFIX


@receiver([post_save, post_delete], sender=Translation)
def invalidate_translation_cache(sender, instance, **kwargs):
    """
    Clear the cache for specific language translations when a translation is updated or deleted
    """
    # Use the DatabaseTranslation method to reset both cache and in-memory translations
    db_translation.reset_translation_cache(instance.language.code)


@receiver([post_save, post_delete], sender=Language)
def invalidate_language_cache(sender, instance, **kwargs):
    """
    Clear all translations cache when language changes
    """
    # Reset all translations when language changes
    db_translation.reset_translation_cache()
