from rest_framework import status
from rest_framework.test import APITestCase
from factory import Faker

from journey.rides.tests.factories import RateFactory, RideFactory
from journey.users.tests.factories import RiderFactory, DriverFactory
from journey.utils.payment_platform import get_acceptance_token, get_tokenized_card

# Create your tests here.
class TestSetUp(APITestCase):

    def setUp(self):
        self.login_url = '/auth-token/'
        self.rider1 = RiderFactory.create()
        self.full_rider = RiderFactory.create_with_payment_source()
        self.driver1 = DriverFactory.create()
        return super().setUp()
    
    def login(self, user):
        response = self.client.post(
            self.login_url,
            {
                'username': user.username,
                'password': 'password1234'
            },
            format='json'
        )
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)


class TestRiders(TestSetUp):
    url = '/api/riders/'

    def setUp(self):
        super().setUp()
        
        self.login(self.rider1.user)
    
    def test_payment_method(self):
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
        self.assertEqual(response.data['payment_source'], self.rider1.payment_source)

    def test_payment_method_invalid_user(self):
        self.login(self.driver1.user)

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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error']['type'], 'PROFILE_VALIDATION_ERROR')
    
    def test_request_ride_whitout_rates(self):
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
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['error']['type'], 
            "RATE_VALIDATION_ERROR"
        )

    def test_request_ride_whitout_payment_method(self):
        RateFactory.create()
        response = self.client.post(
            self.url + 'request_ride/',
            {
                'latitude': Faker("latitude").evaluate(None, None, extra={"locale": None}),
                'longitude': Faker("longitude").evaluate(None, None, extra={"locale": None})
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_428_PRECONDITION_REQUIRED)
        self.assertEqual(
            response.data['error']['type'], 
            "PAYMENT_METHOD_VALIDATION_ERROR"
        )

    def test_request_ride_whitout_driver(self):
        self.login(self.full_rider.user)
        rate = RateFactory.create()
        latitude = Faker("latitude").evaluate(None, None, extra={"locale": None})
        longitude = Faker("longitude").evaluate(None, None, extra={"locale": None})
        RideFactory.create(
            rider=self.full_rider,
            driver=self.driver1,
            rate=rate,
            starting_latitude=latitude,
            starting_longitude=longitude
        )
        response = self.client.post(
            self.url + 'request_ride/',
            {
                'latitude': latitude,
                'longitude': longitude
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data['error']['type'], 
            "AVAILABLE_DRIVERS_VALIDATION_ERROR"
        )

    def test_request_ride_invalid_user(self):
        self.login(self.driver1.user)

        RateFactory.create()
        response = self.client.post(
            self.url + 'request_ride/',
            {
                'latitude': Faker("latitude").evaluate(None, None, extra={"locale": None}),
                'longitude': Faker("longitude").evaluate(None, None, extra={"locale": None})
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data['error']['type'], 
            "PROFILE_VALIDATION_ERROR"
        )

    def test_request_ride_success(self):
        self.login(self.full_rider.user)

        rate = RateFactory.create()
        response = self.client.post(
            self.url + 'request_ride/',
            {
                'latitude': Faker("latitude").evaluate(None, None, extra={"locale": None}),
                'longitude': Faker("longitude").evaluate(None, None, extra={"locale": None})
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['driver']['user']['email'], self.driver1.user.email)
        self.assertEqual(response.data['rate']['id'], rate.id)


class TestDrivers(TestSetUp):
    url = '/api/drivers/'

    def setUp(self):
        super().setUp()
        self.login(self.driver1.user)
        self.driver2 = DriverFactory.create()
        self.latitude = Faker("latitude").evaluate(None, None, extra={"locale": None})
        self.longitude = Faker("longitude").evaluate(None, None, extra={"locale": None})

        self.rate = RateFactory.create()
        self.ride = RideFactory.create(
            rider=self.full_rider,
            driver=self.driver1,
            rate=self.rate,
            starting_latitude=self.latitude,
            starting_longitude=self.longitude
        )
        self.driver2 = DriverFactory.create()

    def test_finish_ride_invalid_user(self):
        self.login(self.rider1.user)
        response = self.client.patch(
            self.url + f'{self.ride.id}/finish_ride/',
            {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_finish_ride_different_driver(self):
        self.login(self.driver2.user)
        response = self.client.patch(
            self.url + f'{self.ride.id}/finish_ride/',
            {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_finish_ride_success(self):
        self.login(self.driver1.user)
        response = self.client.patch(
            self.url + f'{self.ride.id}/finish_ride/',
            {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
