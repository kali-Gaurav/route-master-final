from production_pipeline import api

def test_import_api():
    assert api is not None

def test_hello_world():
    assert "Hello, World!" == "Hello, World!"