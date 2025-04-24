import os
import re
import time
from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands.makemessages import Command as MakeMessagesCommand
from django.conf import settings
from django.utils.translation import to_locale
import polib
from db_translations.utils import extract_messages_from_po_file
from db_translations.models import Language


class Command(BaseCommand):
    help = "Extracts translation strings and stores them in the database"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--locale', '-l', dest='locale', 
            action='append', default=[],
            help='Creates or updates translations for the specified locale(s).'
        )
        parser.add_argument(
            '--all', '-a', action='store_true', dest='all',
            default=False, help='Updates all existing locales.'
        )
        parser.add_argument(
            '--domain', '-d', dest='domain',
            default='django', help='The domain of the message files.'
        )
        parser.add_argument(
            '--ignore', '-i', action='append', dest='ignore_patterns',
            default=[], help='Ignore files or directories matching specified pattern.'
        )
        parser.add_argument(
            '--keep-pot', action='store_true', dest='keep_pot',
            default=False, help='Keep temporary .pot file.'
        )
        parser.add_argument(
            '--extensions', '-e', dest='extensions',
            default=['html', 'txt', 'py'],
            help='List of file extensions to examine.'
        )
        parser.add_argument(
            '--symlinks', '-s', action='store_true', dest='symlinks',
            default=False, help='Follow symlinks.'
        )
        
    def handle(self, *args, **options):
        # Get all active languages if --all is specified
        if options['all']:
            locales = Language.objects.filter(is_active=True).values_list('code', flat=True)
            options['locale'] = [to_locale(lang) for lang in locales]
            
        # Check if we have locales to process
        if not options['locale']:
            raise CommandError('No locales specified. Use --locale or --all.')
        
        # Get original Django makemessages command
        django_command = MakeMessagesCommand()
        
        # Create a temporary directory for PO files
        # We'll use these files and then import them to the database
        original_settings = {}
        temp_locale_dir = os.path.join(os.getcwd(), 'temp_locale')
        
        if os.path.exists(temp_locale_dir):
            # Clean up existing temp directory
            import shutil
            shutil.rmtree(temp_locale_dir)
        
        os.makedirs(temp_locale_dir)
        
        try:
            # Store original settings
            original_settings = {
                'locale_paths': getattr(settings, 'LOCALE_PATHS', []),
                'locale_dir': getattr(settings, 'LOCALE_DIR', None),
            }
            
            # Override settings temporarily
            settings.LOCALE_PATHS = [temp_locale_dir]
            
            # Use Django's makemessages to extract strings to PO files
            options_for_django = options.copy()
            options_for_django['verbosity'] = min(options['verbosity'], 1)  # Reduce verbosity
            django_command.handle(*args, **options_for_django)
            
            # Import PO files into database
            total_created = 0
            total_updated = 0
            
            # Process each locale
            for locale in options['locale']:
                # Convert locale to language code if needed
                language_code = locale.replace('_', '-').lower()
                
                domain = options['domain']
                po_path = os.path.join(temp_locale_dir, locale, 'LC_MESSAGES', f"{domain}.po")
                
                if os.path.exists(po_path):
                    created, updated = extract_messages_from_po_file(po_path, language_code)
                    total_created += created
                    total_updated += updated
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Processed locale '{locale}': {created} new strings, {updated} updated"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"No PO file found for locale '{locale}'")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Translation extraction complete. Total: {total_created} new, {total_updated} updated"
                )
            )
                
        finally:
            # Clean up and restore settings
            if not options.get('keep_pot', False):
                import shutil
                shutil.rmtree(temp_locale_dir, ignore_errors=True)
                
            # Restore original settings
            for key, value in original_settings.items():
                if value is not None:
                    setattr(settings, key, value)
