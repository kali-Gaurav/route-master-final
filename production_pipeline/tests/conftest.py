import pytest

@pytest.fixture(scope='session')
def setup_database():
    pass

@pytest.fixture(scope='function')
def setup_api():
    pass