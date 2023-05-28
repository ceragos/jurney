import os, requests
from collections.abc import Sequence
from typing import Any

from django.contrib.auth import get_user_model
from factory import Faker, post_generation, SubFactory
from factory.django import DjangoModelFactory

from journey.users.models import Rider, Driver


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
    tokenized_card = Faker("credit_card_number")
    
    @post_generation
    def tokenized_card(self, create, extracted, **kwargs):
        if not create:
            return

        # Generar datos fake para la tarjeta
        card_number = Faker("credit_card_number").generate()
        cvc = Faker("credit_card_security_code").generate()
        exp_month = Faker("credit_card_expire").generate().month
        exp_year = Faker("credit_card_expire").generate().year
        card_holder = self.user.name

        api_endpoint = f"{os.environ['WOMPI_HOST']}/tokens/cards"
        api_key = os.environ['WOMPI_PUBLIC_KEY']

        payload = {
            "card_number": card_number,
            "cvc": cvc,
            "exp_month": exp_month,
            "exp_year": exp_year,
            "card_holder": card_holder,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        response = requests.post(api_endpoint, json=payload, headers=headers)

        if response.status_code == 200:
            # Obtener el tokenizado de la tarjeta desde la respuesta de la API
            tokenized_card = response.json().get("tokenized_card")
            self.tokenized_card = tokenized_card

    class Meta:
        model = Rider
