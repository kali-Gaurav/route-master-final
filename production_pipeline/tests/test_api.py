def test_import():
    try:
        import production_pipeline.database
        assert True
    except ImportError:
        assert False, "Import 'production_pipeline.database' could not be resolved"

def test_type_expression():
    variable = 5
    assert isinstance(variable, int)