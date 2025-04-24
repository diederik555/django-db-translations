from django.utils import translation
from .translation import activate_db_translation
from django.utils.translation import trans_real
import functools

class DatabaseTranslationMiddleware:
    """
    Middleware that activates database translations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Store original translation function
        trans_real._original_translation = trans_real.translation
        # Activate database translation backend
        activate_db_translation()
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
