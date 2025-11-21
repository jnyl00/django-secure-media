import django_secure_media as secure_media


auth_policy = secure_media.MediaAccessPolicy(
    restricted_prefixes=('images/', 'profiles/'),
    access_check=lambda request, path: request.user.is_authenticated
)


# Register
secure_media.register(auth_policy)
