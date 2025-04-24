from django.test import TestCase, override_settings
from django.core.cache import cache
from django.utils import translation
from .models import Language, Translation
from .signals import TRANSLATION_CACHE_KEY_PREFIX
from .translation import activate_db_translation


class LanguageModelTestCase(TestCase):
    def test_language_creation(self):
        language = Language.objects.create(code='en', name='English', is_active=True)
        self.assertEqual(str(language), 'English (en)')
        self.assertTrue(Language.objects.filter(code='en').exists())


class TranslationModelTestCase(TestCase):
    def setUp(self):
        self.language = Language.objects.create(code='en', name='English', is_active=True)
        
    def test_translation_creation(self):
        trans = Translation.objects.create(
            language=self.language,
            message_id='Hello world',
            translation='Hello world',
            location='test.py:10'
        )
        self.assertTrue(Translation.objects.filter(message_id='Hello world').exists())
        self.assertIn('Hello world', str(trans))


class DatabaseTranslationTestCase(TestCase):
    def setUp(self):
        # Clear the cache before tests
        cache.clear()
        
        # Create test languages and translations
        self.en = Language.objects.create(code='en', name='English', is_active=True)
        self.es = Language.objects.create(code='es', name='Spanish', is_active=True)
        
        # Create English translations (source)
        Translation.objects.create(
            language=self.en,
            message_id='Hello world',
            translation='Hello world',
        )
        
        Translation.objects.create(
            language=self.en,
            message_id='Welcome {name}',
            translation='Welcome {name}',
        )
        
        # Create Spanish translations
        Translation.objects.create(
            language=self.es,
            message_id='Hello world',
            translation='Hola mundo',
        )
        
        Translation.objects.create(
            language=self.es,
            message_id='Welcome {name}',
            translation='Bienvenido {name}',
        )
        
        # Create translation with context
        Translation.objects.create(
            language=self.es,
            message_id='Post',
            context='verb',
            translation='Publicar',
        )
        
        Translation.objects.create(
            language=self.es,
            message_id='Post',
            context='noun',
            translation='Publicación',
        )
        
        # Activate database translation backend
        activate_db_translation()
        
    def test_basic_translation(self):
        # Test Spanish translation
        with translation.override('es'):
            # This message exists in database
            self.assertEqual(translation.gettext('Hello world'), 'Hola mundo')
            
    def test_context_translation(self):
        with translation.override('es'):
            # Test context-specific translations
            from django.utils.translation import pgettext
            self.assertEqual(pgettext('verb', 'Post'), 'Publicar')
            self.assertEqual(pgettext('noun', 'Post'), 'Publicación')
            
    def test_fallback_to_english(self):
        with translation.override('es'):
            # This message doesn't exist in database
            self.assertEqual(translation.gettext('This is not translated'), 'This is not translated')
            
    def test_cache_invalidation(self):
        # First access will cache the translations
        with translation.override('es'):
            self.assertEqual(translation.gettext('Hello world'), 'Hola mundo')
            
        # Verify the cache key exists
        cache_key = f"{TRANSLATION_CACHE_KEY_PREFIX}_es"
        self.assertIsNotNone(cache.get(cache_key))
        
        # Update a translation
        es_trans = Translation.objects.get(language=self.es, message_id='Hello world')
        es_trans.translation = 'Hola a todos'
        es_trans.save()
        
        # Cache should be invalidated
        self.assertIsNone(cache.get(cache_key))
        
        # New translation should be used
        with translation.override('es'):
            self.assertEqual(translation.gettext('Hello world'), 'Hola a todos')
