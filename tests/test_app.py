from streamlit.testing.v1 import AppTest


def test_app_starts_without_streamlit_exceptions():
    app = AppTest.from_file("app.py").run()
    assert not app.exception, app.exception
