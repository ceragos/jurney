from factory import Faker
from rest_framework import status

from journey.rides.tests.factories import RateFactory
from journey.utils.payment_platform import get_acceptance_token, get_tokenized_card
from journey.rides.tests.test_rides import TestSetUp


class TestIntegration(TestSetUp):
    url = '/api/riders/'

    def setUp(self):
        super().setUp()
        RateFactory.create()
    
    def tests_integration(self):

        self.login(self.rider1.user)
        acceptance_token = get_acceptance_token()
        tokenized_card = get_tokenized_card(self.rider1.user.name)
        response = self.client.patch(
            self.url + 'payment_method/',
            {
                'tokenized_card': tokenized_card,
                'acceptance_token': acceptance_token
            },
            format='json'
        )
        self.rider1.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        latitude = Faker("latitude").evaluate(None, None, extra={"locale": None})
        longitude = Faker("longitude").evaluate(None, None, extra={"locale": None})
        response = self.client.post(
            self.url + 'request_ride/',
            {
                'latitude': latitude,
                'longitude': longitude
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.url = '/api/drivers/'
        ride = response.data['id']
        latitude = Faker("latitude").evaluate(None, None, extra={"locale": None})
        longitude = Faker("longitude").evaluate(None, None, extra={"locale": None})
        self.login(self.driver1.user)
        response = self.client.patch(
            self.url + f'{ride}/finish_ride/',
            {
                'latitude': latitude,
                'longitude': longitude
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
