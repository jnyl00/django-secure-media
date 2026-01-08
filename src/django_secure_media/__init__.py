from typing import Optional

from django.utils.module_loading import autodiscover_modules

from .decorators import secure_media_path
from .policies import MediaAccessPolicy, MediaAccessPolicyRegistry

__all__ = [
    "secure_media_path",
    "MediaAccessPolicy",
    "MediaAccessPolicyRegistry",
    "register",
    "autodiscover",
]


def register(media_policy: 'MediaAccessPolicy', policy_registry: Optional['MediaAccessPolicyRegistry'] = None):
    """
    Register the given `MediaAccessPolicy` instances with policy registry.

    The `registry` kwarg is an policy registry to use instead of the default policy registry.
    """
    from django_secure_media.policies import registry as default_registry

    registry = policy_registry or default_registry

    if not isinstance(registry, MediaAccessPolicyRegistry):
        raise ValueError("registry must subclass MediaAccessPolicyRegistry")

    if not isinstance(media_policy, MediaAccessPolicy):
        raise ValueError("Wrapped class must subclass MediaAccessPolicy.")

    registry.register(media_policy)


def autodiscover():
    autodiscover_modules('media_policies')
