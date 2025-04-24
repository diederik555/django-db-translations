from django.utils import translation
from .translation import activate_db_translation


class DatabaseTranslationMiddleware:
    """
    Middleware that activates database translations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Activate database translation backend
        activate_db_translation()
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
