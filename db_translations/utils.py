import os
import re
import polib
import tempfile
from django.conf import settings
from django.utils import translation
from .models import Translation, Language


def extract_messages_from_po_file(po_file_path, language_code):
    """
    Extract messages from a .po file and store them in the database
    """
    try:
        language = Language.objects.get(code=language_code)
    except Language.DoesNotExist:
        # Create language if it doesn't exist
        language = Language.objects.create(
            code=language_code,
            name=language_code,  # Simple name based on code
            is_active=True
        )
    
    po = polib.pofile(po_file_path)
    created = 0
    updated = 0
    
    for entry in po:
        # Skip obsolete entries
        if entry.obsolete:
            continue
            
        location = ''
        if entry.occurrences:
            # Get the first occurrence location
            location = f"{entry.occurrences[0][0]}:{entry.occurrences[0][1]}"
        
        trans_obj, created_new = Translation.objects.update_or_create(
            language=language,
            message_id=entry.msgid,
            context=entry.msgctxt or '',
            defaults={
                'translation': entry.msgstr,
                'location': location[:255],  # Limit to field length
            }
        )
        
        if created_new:
            created += 1
        else:
            updated += 1
    
    return created, updated


def create_temp_po_file(extracted_strings):
    """
    Create a temporary .po file from extracted strings
    """
    po = polib.POFile()
    po.metadata = {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
    }
    
    for message_data in extracted_strings:
        entry = polib.POEntry(
            msgid=message_data['msgid'],
            msgctxt=message_data.get('msgctxt', None),
            occurrences=message_data.get('occurrences', []),
            comment=message_data.get('comment', ''),
        )
        po.append(entry)
    
    # Create temp file
    fd, path = tempfile.mkstemp(suffix='.po')
    os.close(fd)
    
    po.save(path)
    return path


def sync_translation_with_db(language_code, extracted_strings):
    """
    Synchronize extracted strings with database
    """
    # Create a temporary PO file
    po_path = create_temp_po_file(extracted_strings)
    
    try:
        # Process the temporary PO file
        created, updated = extract_messages_from_po_file(po_path, language_code)
        return created, updated
    finally:
        # Clean up the temporary file
        os.unlink(po_path)
