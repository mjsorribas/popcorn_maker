import base64
import hashlib

from django.contrib.auth.models import User


def create_user(handle, use_hash=False):
    """Helper to create Users"""
    email = '%s@%s.com' % (handle, handle)
    if use_hash:
        username = base64.urlsafe_b64encode(
            hashlib.sha1(email).digest()).rstrip('=')
    else:
        username = handle
    return User.objects.create_user(username, email, handle)
