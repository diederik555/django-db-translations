from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Translation, Language

# Cache key prefix for translations
TRANSLATION_CACHE_KEY_PREFIX = 'db_translations'


@receiver([post_save, post_delete], sender=Translation)
def invalidate_translation_cache(sender, instance, **kwargs):
    """
    Clear the cache for specific language translations when a translation is updated or deleted
    """
    # Clear cache for the specific language
    language_key = f"{TRANSLATION_CACHE_KEY_PREFIX}_{instance.language.code}"
    cache.delete(language_key)
    
    # Also clear the combined cache key
    cache.delete(TRANSLATION_CACHE_KEY_PREFIX)


@receiver([post_save, post_delete], sender=Language)
def invalidate_language_cache(sender, instance, **kwargs):
    """
    Clear all translations cache when language changes
    """
    # When a language is updated, all cached translations may be affected
    cache.delete(TRANSLATION_CACHE_KEY_PREFIX)
    
    # Also clear cache for the specific language
    language_key = f"{TRANSLATION_CACHE_KEY_PREFIX}_{instance.code}"
    cache.delete(language_key)
