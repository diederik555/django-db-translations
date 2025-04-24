# Django Database Translations
Django Database Translations is a powerful Django application that replaces the traditional .po/.mo file-based translation system with a database-backed translation store. This approach makes translations more dynamic, easier to manage through the Django admin interface, and eliminates the need to compile translation files after changes.

## Features

- Store all translations in the database instead of .po/.mo files
- Full integration with Django's built-in translation system
- Admin interface for managing translations
- Automatic cache management with intelligent invalidation
- Context-based translations support (pgettext)
- Fallback to Django's default translation system when strings aren't found
- Import/export functionality with standard .po files
- Middleware for easy activation

## Installation

### Requirements

- Python 3.8+
- Django 3.2+

### Install the package

```shell script
pip install django-db-translations
```


### Update settings.py

Add `'db_translations'` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'db_translations',
    ...
]
```


### Add the middleware

Add the middleware to your `MIDDLEWARE` list:

```python
MIDDLEWARE = [
    ...
    'db_translations.middleware.DatabaseTranslationMiddleware',
    ...
]
```


### Migrate the database

Run migrations to create the necessary database tables:

```shell script
python manage.py makemigrations db_translations
python manage.py migrate db_translations
```


## Configuration Options

Add these optional settings to your Django settings.py file:

```python
# Cache timeout for database translations (default is 24 hours)
DB_TRANSLATIONS_CACHE_TIMEOUT = 60 * 60 * 24  # in seconds
```


## Usage

### Basic Usage

Once installed and configured, the package automatically integrates with Django's translation system. You can use all of Django's standard translation functions, and the translations will be looked up in the database:

```python
from django.utils.translation import gettext as _

# This will look up the translation in the database
translated_text = _("Hello world")
```


### Using the Admin Interface

The package provides a user-friendly admin interface for managing languages and translations:

1. Navigate to the Django admin interface
2. Look for the "Database Translations" section
3. Add languages and translations as needed

### Adding Languages

1. Go to the admin interface
2. Click on "Languages" under "Database Translations"
3. Add a new language with:
   - Code: The language code (e.g., 'en', 'es', 'fr')
   - Name: The human-readable name (e.g., 'English', 'Spanish', 'French')
   - Is active: Whether the language is active for translation

### Adding Translations

1. Go to the admin interface
2. Click on "Translations" under "Database Translations"
3. Add a new translation with:
   - Language: Select the language
   - Message ID: The original untranslated string
   - Translation: The translated text
   - Context (optional): For disambiguating strings with multiple meanings
   - Location (optional): File location reference

### Context-Based Translations

For strings that have different meanings in different contexts, use context-based translations:

```python
from django.utils.translation import pgettext

# This will look up a translation with 'verb' context
action_button = pgettext('verb', 'Post')

# This will look up a translation with 'noun' context
blog_title = pgettext('noun', 'Post')
```


### Importing Translations from PO Files

If you already have .po files, you can import them into the database:

```python
from db_translations.utils import extract_messages_from_po_file

# Import translations from a .po file for a specific language
extract_messages_from_po_file('path/to/locale/es/LC_MESSAGES/django.po', 'es')
```


### Exporting Translations to PO Files

You can also export translations from the database to .po files (useful for sharing with external translators):

```python
# This functionality would need to be implemented as it's not directly provided in the code samples
```


## How It Works

Django Database Translations works by monkey-patching Django's translation system to use database lookups instead of the default .mo file lookups:

1. When `activate_db_translation()` is called (via middleware or in your code), it replaces Django's translation function.
2. When a translation is requested via `gettext()` or similar functions, it first looks in the database.
3. If not found in the database, it falls back to Django's default translation.
4. Translations are cached for performance and automatically invalidated when updated.

## Performance Considerations

Database translations are efficiently cached to minimize database queries:

- All translations for a language are fetched and cached in a single operation
- Cache is automatically invalidated when translations are updated
- Cache timeout is configurable via settings (default is 24 hours)

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! Feel free to submit pull requests or open issues on our GitHub repository.

## Support

If you encounter any problems or have questions, please open an issue on our GitHub repository.
