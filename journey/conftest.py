import pytest

from journey.users.models import User, Rider, Driver
from journey.users.tests.factories import UserFactory, RiderFactory, DriverFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> User:
    return UserFactory()


@pytest.fixture
def rider(db) -> Rider:
    return RiderFactory()


@pytest.fixture
def driver(db) -> Driver:
    return DriverFactory()
