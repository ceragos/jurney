from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db.models import PointField


class User(AbstractUser):
    """
    Default custom user model for journey.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class Driver(models.Model):
    user = models.ForeignKey(User, verbose_name="user", on_delete=models.PROTECT, related_name="driver_user")
    current_location = PointField()

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"
    

class Rider(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="driver_user")
    tokenized_card = models.CharField(max_length=50, null=True, help_text="data created in the payment api")

    def __str__(self) -> str:
        return f"{self.user.first_name} {self.user.last_name}"
