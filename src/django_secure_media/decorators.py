from functools import wraps
from typing import TYPE_CHECKING, Optional, Callable

from django.http import Http404

if TYPE_CHECKING:
    from .policies import MediaAccessPolicyRegistry


def secure_media_path(function: Optional[Callable] = None, policy_registry: Optional['MediaAccessPolicyRegistry'] = None):
    """
    Decorator that wraps a view to enforce multiple media access policies.
    """
    from django_secure_media.policies import registry as default_registry

    def decorator(view_func):
        def check_path(request, path, *args, **kwargs):
            registry = policy_registry or default_registry

            if not registry.is_allowed(request, path):
                raise Http404("Restricted media file")
            return view_func(request, path, *args, **kwargs)
        return wraps(view_func)(check_path)

    if callable(function):
        return decorator(function)
    return decorator
