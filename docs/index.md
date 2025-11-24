---
title: Introduction
---

# Django Secure Media

A simple secure `Media` access system for Django.


## Overview

Django’s built-in static and media file serving views do not provide access control out of the box.
This Secure Media Access system introduces a flexible, policy-based mechanism to grant access to specific media directories based on the incoming request and the file path.

You can use it to:

- Prevent unauthenticated users from viewing profile pictures or private uploads.
- Restrict sensitive folders to staff or admin users.
- Define per-directory rules dynamically and cleanly.

## Architecture

The system is built around three main components:

1. `MediaAccessPolicy` – defines a single access rule (what paths it applies to and how to check access).
2. `MediaAccessPolicyRegistry` – manages multiple policies and selects the right one for each request.
3. `secure_media_path` decorator – applies the registry’s logic to a Django view (such as `django.views.static.serve`).

!!! note 

    It is similar to the `django.contrib.admin` application.

### 1. MediaAccessPolicy


```python
class MediaAccessPolicy:
    def __init__(self, restricted_prefixes: tuple[str, ...], access_check: Callable):
        """
        Create a media access policy.

        :param restricted_prefixes: Tuple of directory prefixes this policy covers.
                                    Example: ('images/', 'profiles/')
        :param access_check: Callable taking (request, path) and returning True if access is allowed.
                             Example: lambda request, path: request.user.is_authenticated
        """
```

#### Methods

| Method                    | Description                                                         |
| ------                    | -----------                                                         |
| matches(path)             | Returns True if the path starts with any of this policy’s prefixes. |
| is_allowed(request, path) | Returns True if the access_check function approves access.          |

#### Example

```python
from django_secure_media.policies import MediaAccessPolicy

...

auth_policy = MediaAccessPolicy(
    restricted_prefixes=('images/',),
    access_check=lambda request, path: request.user.is_authenticated
)
```

### 2. MediaAccessPolicyRegistry


```python
class MediaAccessPolicyRegistry:
    def __init__(self, policies: Iterable[MediaAccessPolicy] = (), default_allow=True):
        """
        Manages a collection of media access policies.

        :param policies: Optional iterable of MediaAccessPolicy instances.
        :param default_allow: If True, paths without a matching policy are allowed by default.
        """
```

#### Methods

| Method                    | Description                                                        |
| ------                    | -----------                                                        |
| register(policy)          | Add a new MediaAccessPolicy to the registry.                       |
| get_policy_for_path(path) | Return the first matching policy for the given path.               |
| is_allowed(request, path) | Return True if the appropriate policy (if any) allows the request. |

#### Example

```python
import django_secure_media as secure_media
from django_secure_media.policies import MediaAccessPolicyRegistry

...

registry = MediaAccessPolicyRegistry(default_allow=False)  # custom

registry.register(auth_policy)
registry.register(staff_policy)

# OR (Custom registry)

secure_media.register(auth_policy, policy_registry=registry)
secure_media.register(staff_policy, policy_registry=registry)

# OR (Default registry)

secure_media.register(auth_policy)
secure_media.register(staff_policy)
```

### 3. secure_media_path


```python
def secure_media_path(function: Optional[Callable] = None, policy_registry: Optional['MediaAccessPolicyRegistry'] = None):
    """
    Decorator that wraps a view to enforce multiple media access policies.

    Usage:
        @secure_media_path(policy_registry=registry)
        def my_media_view(request, path):
            ...
    """
```

#### Behavior

When a view wrapped by `secure_media_path()` is called:

1. The decorator asks the registry whether access is allowed for (request, path).
2. If no policy allows access, a Http404("Restricted media file") is raised.
3. Otherwise, the wrapped view (e.g. serve()) is executed normally.

### Flow Diagram

```
                   ┌────────────────────────────────────────┐
                   │          Incoming Request              │
                   │  e.g. /media/profiles/john/avatar.png  │
                   └────────────────────────────────────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────────┐
                     │    secure_media_path decorator     │
                     │  (applied to the media view)       │
                     └────────────────────────────────────┘
                                      │
                        calls registry.is_allowed(request, path)
                                      │
                                      ▼
         ┌──────────────────────────────────────────────────────────┐
         │              MediaAccessPolicyRegistry                   │
         │  ┌────────────────────────────────────────────────────┐  │
         │  │  Finds first matching MediaAccessPolicy            │  │
         │  │  based on path prefixes                            │  │
         │  └────────────────────────────────────────────────────┘  │
         └──────────────────────────────────────────────────────────┘
                                      │
                   ┌──────────────────┴───────────────────┐
                   │                                      │
         ┌──────────────────────┐               ┌──────────────────────┐
         │  MediaAccessPolicy   │               │  MediaAccessPolicy   │
         │  (e.g. profiles/)    │               │  (e.g. images/)      │
         │  calls access_check  │               │  calls access_check  │
         │  (request, path)     │               │  (request, path)     │
         └──────────────────────┘               └──────────────────────┘
                   │                                      │
         allow? ───┘                                      │
                   │                                      │
                   ▼                                      ▼
       ┌──────────────────────┐             ┌──────────────────────┐
       │  Serve view executes │             │  Raise Http404       │
       │  (file is delivered) │             │  (access denied)     │
       └──────────────────────┘             └──────────────────────┘
```

**Flow Description**

1. Request arrives for a media URL, e.g. /media/profiles/john/avatar.png.
2. The secure_media_path decorator intercepts the request.
3. It asks the MediaAccessPolicyRegistry whether access is allowed.
4. The registry checks each registered MediaAccessPolicy in order:
	- Finds the first that matches the requested path prefix.
	- Calls that policy’s access_check(request, path) to make a decision.
5. If allowed → the original view (e.g. Django’s serve()) runs and the file is delivered.<br/>
   If denied → a Http404("Restricted media file") is raised.

---

## Example

### Setup

Here we use the default media access policy registry instance.

```python title="media_policies.py"
import django_secure_media as secure_media


# Custom path-aware access check
def user_owns_profile(request, path):
    if not request.user.is_authenticated:
        return False
    expected_prefix = f"profiles/{request.user.username}/"
    return str(path).startswith(expected_prefix)

# Define policies
auth_policy = secure_media.MediaAccessPolicy(
    restricted_prefixes=('images/',),
    access_check=lambda request, path: request.user.is_authenticated
)

profile_policy = secure_media.MediaAccessPolicy(
    restricted_prefixes=('profiles/',),
    access_check=user_owns_profile
)

# Combine policies into a registry
secure_media.register(auth_policy)
secure_media.register(profile_policy)
```

```python title="urls.py"
from django.conf import settings
from django.views.static import serve

from django_secure_media.decorators import secure_media_path


# Protect Django's media serving view
urlpatterns = [
    path(
        'media/<path:path>/',
        secure_media_path(serve),
        {'document_root': settings.MEDIA_ROOT},
    ),
]
```

### Scenarios

| Path                                                           | User            | Result                         | Policy Triggered |
| ----                                                           | ----            | ------                         | ---------------- |
| /media/images/banner.png                                       | Unauthenticated | ❌ Denied                      | auth_policy      |
| /media/images/banner.png                                       | Authenticated   | ✅ Allowed                     | auth_policy      |
| /media/profiles/jane/avatar.png                                | user=jane       | ✅ Allowed                     | profile_policy   |
| /media/profiles/john/avatar.png                                | user=jane       | ❌ Denied                      | profile_policy   |
| /media/public/file.txt                                         | Anyone          | ✅ Allowed                     | —                |
| When custom MediaAccessPolicyRegistry with default_allow=False |                 |                                |                  |
| /media/public/file.txt                                         | Anyone          | ❌ Denied (no matching policy) | —                |

---

## Testing

!!! warning
    Must be implemented

---

## Extending the System

This design is intentionally extensible:

- Add roles or permissions:
    ```python
    staff_policy = MediaAccessPolicy(
        ('admin_docs/',),
        lambda r, p: getattr(r.user, "is_staff", False)
    )
    ```

- Integrate with Django settings:

    You can dynamically load prefixes and checks from a custom setting like MEDIA_ACCESS_POLICIES.

- Add logging:

    Inside the decorator, you can log denied access attempts:

    ```python
    import logging
    logger = logging.getLogger(__name__)
    ...
    if not policy_registry.is_allowed(request, path):
        logger.warning(f"Access denied to {path} by {request.user}")
        raise Http404("Restricted media file")
    ```

---

## Production

In development, `Django` can serve media files directly using `django.views.static.serve`, but in production, you should serve media files via a web server like Nginx or Apache. 
The secure_media_path system can still be applied, either directly via Django views (for dynamic access control) or as part of an API endpoint.


1. Serving Media via Django Views (Dynamic Access Control)

    Even in production, you may want dynamic, per-user checks. For example, profile images or private uploads.

    ```python title="urls.py"
    from django.urls import path
    from django.conf import settings
    from django.views.static import serve
    from django_secure_media.decorators import secure_media_path
    from django_secure_media.policies import MediaAccessPolicy, MediaAccessPolicyRegistry

    def user_owns_profile(request, path):
        if not request.user.is_authenticated:
            return False
        return str(path).startswith(f"profiles/{request.user.username}/")

    profile_policy = MediaAccessPolicy(
        restricted_prefixes=('profiles/',),
        access_check=user_owns_profile
    )

    registry = MediaAccessPolicyRegistry(default_allow=False)
    registry.register(profile_policy)

    urlpatterns = [
        path(
            'media/<path:path>/',
            secure_media_path(serve, policy_registry=registry),
            # OR
            #secure_media_path(policy_registry=registry)(serve),
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
    ```

    ✅ Pros:

    - Fine-grained per-request access control
    - Works for authenticated users, staff, or custom policies

    ❌ Cons:

    - Django is slower than Nginx for serving static files
    - Not ideal for large-scale media serving


2. Serving Media via Nginx with Django Authorization
    For large projects, you can combine Django for access checks and Nginx for actual file serving:

    1. Django endpoint:
        - Checks access using secure_media_path.
        - Returns a temporary URL or redirects to Nginx’s internal location.
    2. Nginx configuration:
        ```text
        location /protected_media/ {
            internal;  # cannot be accessed directly
            alias /var/www/project/media/;
        }
        ```
    3. Django view returns internal redirect:
        ```python
        from django.http import HttpResponse
        from django.shortcuts import redirect
        from django_secure_media.policies import registry  # This is the default registry

        def protected_media_view(request, path):
            if not registry.is_allowed(request, path):
                raise Http404()
            # Nginx internal redirect
            response = HttpResponse()
            response['X-Accel-Redirect'] = f"/protected_media/{path}"
            return response
        ```

        ✅ Pros:

        - Media files served efficiently by Nginx
        - Access checks still performed in Django


3. Serving Media via Django REST Framework
    If your app exposes media via an API, policies can be enforced per user or token.

    ```python
    from rest_framework.decorators import api_view, permission_classes
    from rest_framework.permissions import IsAuthenticated
    from rest_framework.response import Response
    from django_secure_media.policies import registry  # This is the default registry

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def profile_image(request, username, filename):
        path = f"profiles/{username}/{filename}"
        if not registry.is_allowed(request, path):
            return Response({"detail": "Not allowed"}, status=404)
        file_path = settings.MEDIA_ROOT / path
        with open(file_path, 'rb') as f:
            return Response(f.read(), content_type='image/jpeg')
    ```

    ✅ Pros:

    - Works for API clients
    - Supports token-based authentication
    - Compatible with mobile apps

---

Recommendations

- Use Django + secure_media_path for low-volume dynamic access control.
- Use Nginx + Django authorization for high-volume production serving.
- Combine with DRF endpoints for API-based media delivery.
- Always validate user access at the Django layer — never rely on path secrecy alone.
