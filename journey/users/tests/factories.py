from collections.abc import Sequence
from typing import Any
from django.contrib.auth import get_user_model
from factory import Faker, SubFactory, post_generation
from factory.django import DjangoModelFactory

from journey.users.models import Rider, Driver
from journey.utils.payment_platform import get_acceptance_token, get_payment_source, get_tokenized_card


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create: bool, extracted: Sequence[Any], **kwargs):
        password = (
            extracted
            if extracted
            else Faker(
                "password",
                length=42,
                special_chars=True,
                digits=True,
                upper_case=True,
                lower_case=True,
            ).evaluate(None, None, extra={"locale": None})
        )
        self.set_password(password)

    class Meta:
        model = get_user_model()
        django_get_or_create = ["username"]


class DriverFactory(DjangoModelFactory):
    user = SubFactory(UserFactory, password="password1234")
    current_latitude = Faker("latitude")
    current_longitude = Faker("longitude")

    class Meta:
        model = Driver


class RiderFactory(DjangoModelFactory):
    user = SubFactory(UserFactory, password="password1234")

    @classmethod
    def create_with_payment_source(cls, **kwargs):
        rider = cls.create(**kwargs)
        tokenized_card = get_tokenized_card(rider.user.name)
        acceptance_token = get_acceptance_token()
        payment_source = get_payment_source(tokenized_card, acceptance_token, rider.user.email)
        rider.payment_source = payment_source['payment_source']
        rider.save()
        return rider

    class Meta:
        model = Rider
