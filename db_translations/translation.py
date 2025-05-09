import functools
from django.utils.translation import trans_real
from django.core.cache import cache
from threading import local
from django.conf import settings
from .models import Translation, Language
from .constants import TRANSLATION_CACHE_KEY_PREFIX


class DatabaseTranslation:
    """
    Database-backed translation engine that replaces Django's gettext with
    a version that fetches translations from the database.
    """
    def __init__(self):
        # The original _DJANGO_TRANSLATION attribute
        self._original_django_translations = {}
        # Thread-local storage for tracking translation state
        self._local = local()
        # Cache timeout (default to 24 hours)
        self.cache_timeout = getattr(settings, 'DB_TRANSLATIONS_CACHE_TIMEOUT', 60 * 60 * 24)
    
    def get_language_from_db(self, lang_code):
        """Get language object from database or return None"""
        try:
            return Language.objects.get(code=lang_code, is_active=True)
        except Language.DoesNotExist:
            return None
    
    def fetch_translations_from_db(self, lang_code):
        """Fetch all translations for a specific language from the database"""
        language = self.get_language_from_db(lang_code)
        if not language:
            return {}
            
        translations = {}
        for trans in Translation.objects.filter(language=language):
            key = trans.message_id
            if trans.context:
                # Handle context-specific translations
                key = f"{trans.context}\x04{trans.message_id}"
            translations[key] = trans.translation
        
        return translations
    
    def get_translations_dict(self, lang_code):
        """Get translations dictionary for a language, using cache"""
        cache_key = f"{TRANSLATION_CACHE_KEY_PREFIX}_{lang_code}"
        translations = cache.get(cache_key)
        
        if translations is None:
            translations = self.fetch_translations_from_db(lang_code)
            cache.set(cache_key, translations, self.cache_timeout)
            
        return translations
    
    def translation(self, language):
        """
        Returns a translation object for a language.
        This overrides Django's get_translation function to use database translations.
        """
        # Check if we're already in a translation lookup to prevent recursion
        if getattr(self._local, 'in_translation', False):
            return self._get_original_translation(language)

        # Set the translation lookup flag
        self._local.in_translation = True
        
        # Get the original Django translation object
        try:
            django_translation = self._get_original_translation(language)
        finally:
            # Always clear the translation lookup flag
            self._local.in_translation = False

        # If we've already patched this translation object, return it
        if hasattr(django_translation, '_db_patched'):
            return django_translation
            
        # Store the original _info dict
        if language not in self._original_django_translations:
            self._original_django_translations[language] = {
                'ugettext': django_translation.gettext,
                'ungettext': django_translation.ngettext,
                'upgettext': getattr(django_translation, 'pgettext', None),
                'upngettext': getattr(django_translation, 'npgettext', None),
            }
        
        # Get translations from database
        translations = self.get_translations_dict(language)
        
        # Replace the gettext functions
        def db_gettext(message):
            result = translations.get(message, '')
            if not result:
                # Fallback to original Django translation
                result = self._original_django_translations[language]['ugettext'](message)
            return result
        
        def db_ngettext(singular, plural, number):
            if number == 1:
                result = translations.get(singular, '')
                if not result:
                    result = self._original_django_translations[language]['ungettext'](singular, plural, 1)
                return result
            else:
                result = translations.get(plural, '')
                if not result:
                    result = self._original_django_translations[language]['ungettext'](singular, plural, number)
                return result
        
        def db_pgettext(context, message):
            context_message = f"{context}\x04{message}"
            result = translations.get(context_message, '')
            if not result and self._original_django_translations[language]['upgettext']:
                result = self._original_django_translations[language]['upgettext'](context, message)
            return result or message
        
        def db_npgettext(context, singular, plural, number):
            if number == 1:
                context_message = f"{context}\x04{singular}"
                result = translations.get(context_message, '')
                if not result and self._original_django_translations[language]['upngettext']:
                    result = self._original_django_translations[language]['upngettext'](context, singular, plural, 1)
                return result or singular
            else:
                context_message = f"{context}\x04{plural}"
                result = translations.get(context_message, '')
                if not result and self._original_django_translations[language]['upngettext']:
                    result = self._original_django_translations[language]['upngettext'](context, singular, plural, number)
                return result or plural
        
        # Replace the translation methods
        django_translation.gettext = db_gettext
        django_translation.ngettext = db_ngettext
        
        # Also patch the callable attribute versions
        django_translation.gettext_noop = lambda message: message
        django_translation.pgettext = db_pgettext
        django_translation.npgettext = db_npgettext
        
        # Mark this translation object as patched
        django_translation._db_patched = True
        
        return django_translation

    def _get_original_translation(self, language):
        """
        Get the original Django translation object without our override
        """
        original_translation_func = getattr(trans_real, '_original_translation', trans_real.translation)
        return original_translation_func(language)

    def reset_translation_cache(self, lang_code=None):
        """
        Reset both the Redis cache and the in-memory translation objects.
        If lang_code is provided, only reset for that language.
        """
        if lang_code:
            # Clear specific language cache
            cache_key = f"{TRANSLATION_CACHE_KEY_PREFIX}_{lang_code}"
            cache.delete(cache_key)
            # Remove from our original translations dict
            if lang_code in self._original_django_translations:
                del self._original_django_translations[lang_code]
        else:
            # Clear all language caches
            cache.delete(TRANSLATION_CACHE_KEY_PREFIX)
            # Clear all our original translations
            self._original_django_translations.clear()
            
        # Clear Django's internal translation cache to force reload
        trans_real._translations.clear()
    

# Create a singleton instance
db_translation = DatabaseTranslation()


def activate_db_translation():
    """
    Override Django's translation function with our database-backed version.
    This should be called in AppConfig.ready()
    """
    # Monkey patch Django's translation function
    trans_real.translation = db_translation.translation


def clear_translations():
    """
    Clear Django's in-memory translation objects to force reloading translations from database.
    This should be called when translations are updated.
    """
    # Clear Django's internal translation cache
    trans_real._translations.clear()
    
    # Clear our db_translation patched objects cache
    db_translation._original_django_translations.clear()
