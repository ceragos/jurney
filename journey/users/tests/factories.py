from collections.abc import Sequence
from typing import Any
from django.contrib.auth import get_user_model
from factory import Faker, post_generation, SubFactory
from factory.django import DjangoModelFactory

from journey.users.models import Rider, Driver
from journey.utils.payment_platform import get_acceptance_token, get_payment_sources, get_tokenized_card

fake = Faker()


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
    user = SubFactory(UserFactory)
    current_latitude = Faker("latitude")
    current_longitude = Faker("longitude")

    class Meta:
        model = Driver


class RiderFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    payment_source = Faker("bank")
    
    @post_generation
    def payment_source(self, create, extracted, **kwargs):
        tokenized_card = get_tokenized_card(self.user.name)
        acceptance_token = get_acceptance_token()
        self.payment_source = get_payment_sources(tokenized_card, acceptance_token, self.user.email)

    class Meta:
        model = Rider
