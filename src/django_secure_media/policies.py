import os
from typing import Callable, Iterable

from django.apps import apps
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from django.utils.translation import gettext as _


class MediaAccessPolicy:
    """
    Defines a rule for restricting access to certain media path prefixes.
    """
    def __init__(self, restricted_prefixes: tuple[str, ...], access_check: Callable):
        self.restricted_prefixes = restricted_prefixes
        self.access_check = access_check

    def __repr__(self):
        return f"{self.__class__.__name__}(restricted_prefixes={self.restricted_prefixes!r}, access_check={self.access_check!r})"

    def matches(self, path: str | bytes) -> bool:
        """
        Return `True` if the given path falls under this policy's prefixes.
        """
        tmp_path = os.fspath(path)
        if isinstance(tmp_path, bytes):
            prefixes = tuple(p.encode() for p in self.restricted_prefixes)
        else:
            prefixes = self.restricted_prefixes
        return tmp_path.startswith(prefixes)

    def is_allowed(self, request, path: str | bytes) -> bool:
        """
        Return `True` if the policy allows the given request.
        """
        return self.access_check(request, path)


class MediaAccessPolicyRegistry:
    """
    Manages multiple media access policies and selects one based on path.
    """
    def __init__(self, policies: Iterable[MediaAccessPolicy] = (), default_allow=True):
        self.policies = list(policies)
        self.default_allow = default_allow

    def __repr__(self):
        return f"{self.__class__.__name__}(policies={self.policies!r}, default_allow={self.default_allow!r})"

    def register(self, policy: MediaAccessPolicy):
        """
        Register an additional policy.
        """
        self.policies.append(policy)

    def get_policy_for_path(self, path: str | bytes) -> MediaAccessPolicy | None:
        """
        Return the first matching policy for a path.
        """
        for policy in self.policies:
            if policy.matches(path):
                return policy
        return None

    def is_allowed(self, request, path: str | bytes) -> bool:
        """
        Return whether the given request is allowed to access the path.
        """
        policy = self.get_policy_for_path(path)
        if policy:
            return policy.is_allowed(request, path)
        return self.default_allow


class DefaultMediaAccessPolicyRegistry(LazyObject):
    def _setup(self):
        MediaAccessPolicyRegistryClass = import_string(apps.get_app_config("django_secure_media").default_registry)
        self._wrapped = MediaAccessPolicyRegistryClass()

    def __repr__(self):
        return repr(self._wrapped)


# This global object represents the default policy registry, for the common case.
# You can provide your own MediaAccessPolicyRegistry using the DjangoSecureMediaConfig.default_registry
# attribute.
# You can also instantiate MediaAccessPolicyRegistry in your own code to create a custom registry.
registry = DefaultMediaAccessPolicyRegistry()
