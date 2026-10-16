"""Invalidate cached public campus data when source records change."""
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Building, University


def _bump_building_cache_version(**kwargs):
    key = "campus:building_cache_version"
    # cache.incr is atomic on supported backends. Initialize the key on first use.
    if not cache.add(key, 2, timeout=None):
        try:
            cache.incr(key)
        except (ValueError, NotImplementedError):
            cache.set(key, int(cache.get(key, 1)) + 1, timeout=None)


@receiver(post_save, sender=Building)
@receiver(post_delete, sender=Building)
@receiver(post_save, sender=University)
@receiver(post_delete, sender=University)
def invalidate_public_building_cache(sender, **kwargs):
    _bump_building_cache_version()
