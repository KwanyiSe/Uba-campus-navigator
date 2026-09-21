from urllib.parse import quote

from django.conf import settings
from storages.backends.s3 import S3Storage


class SupabaseBaseStorage(S3Storage):
    """
    S3-compatible storage backend for Supabase Storage.

    Files are uploaded through Supabase's S3 endpoint, while URLs are
    returned through the public Supabase Storage endpoint.
    """

    endpoint_url = settings.SUPABASE_S3_ENDPOINT
    region_name = settings.SUPABASE_S3_REGION
    access_key = settings.SUPABASE_S3_ACCESS_KEY_ID
    secret_key = settings.SUPABASE_S3_SECRET_ACCESS_KEY

    addressing_style = "path"
    default_acl = None
    querystring_auth = False

    def url(self, name):
        if not name:
            return None

        return (
            f"{settings.SUPABASE_PUBLIC_STORAGE_URL}/"
            f"{self.bucket_name}/"
            f"{quote(name, safe='/')}"
        )


class ProfileMediaStorage(SupabaseBaseStorage):
    bucket_name = settings.SUPABASE_S3_PROFILES_BUCKET


class NewsMediaStorage(SupabaseBaseStorage):
    bucket_name = settings.SUPABASE_S3_NEWS_BUCKET
