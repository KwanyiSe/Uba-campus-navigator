from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
#Kwanyise@
from campus.models import University
from .models import Profile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Guarantee that every newly-created Django user has a UNIMAP profile."""
    if not created or hasattr(instance, "profile"):
        return

    university = University.objects.filter(active=True).order_by("id").first()
    if university:
        Profile.objects.create(user=instance, university=university, role="student")
