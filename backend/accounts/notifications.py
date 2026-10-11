from django.utils import timezone
from .models import Notification, Profile


def notify_profile(profile, title, body="", notification_type="general", link=""):
    if not profile:
        return None
    return Notification.objects.create(
        recipient=profile,
        notification_type=notification_type,
        title=title,
        body=body,
        link=link,
    )


def notify_profiles(profiles, title, body="", notification_type="general", link=""):
    profiles = list(profiles)
    if not profiles:
        return 0
    Notification.objects.bulk_create([
        Notification(
            recipient=profile,
            notification_type=notification_type,
            title=title,
            body=body,
            link=link,
        ) for profile in profiles
    ])
    return len(profiles)


def mark_read(notification):
    if notification and notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
