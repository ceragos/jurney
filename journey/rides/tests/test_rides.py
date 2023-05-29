from rest_framework import status
from rest_framework.test import APITestCase

from journey.users.tests.factories import RiderFactory, DriverFactory
from journey.utils.payment_platform import get_acceptance_token, get_tokenized_card

# Create your tests here.
class TestSetUp(APITestCase):

    def setUp(self):

        self.login_url = '/auth-token/'
        self.rider = RiderFactory.create()
        self.full_rider = RiderFactory.create_with_payment_source()
        
        self.driver1 = DriverFactory.create()
        self.driver2 = DriverFactory.create()
        self.driver3 = DriverFactory.create()
        
        response = self.client.post(
            self.login_url,
            {
                'username': self.rider.user.username,
                'password': 'password1234'
            },
            format='json'
        )
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        return super().setUp()


class TestRide(TestSetUp):
    url = '/api/rider/'
    
    def test_payment_method(self):
        acceptance_token = get_acceptance_token()
        tokenized_card = get_tokenized_card(self.rider.user.name)
        response = self.client.patch(
            self.url + 'payment_method/',
            {
                'tokenized_card': tokenized_card,
                'acceptance_token': acceptance_token
            },
            format='json'
        )
        self.rider.refresh_from_db()
        self.assertEqual(response.data['payment_source'], self.rider.payment_source)
    
    def test_request_ride(self):
        self.assertEqual(1, 1)
