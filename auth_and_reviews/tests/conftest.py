import pytest
from app import create_app, db
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope="module")
def test_client():
    flask_app = create_app(TestConfig)

    with flask_app.test_client() as testing_client:
        with flask_app.app_context():
            # 3. Tạo bảng trong DB giả
            from app import models  # noqa: F401

            db.create_all()
            yield testing_client  # --> Trả về client để dùng trong các file test

            # 4. Dọn dẹp sau khi test xong (Teardown)
            db.session.remove()
            db.drop_all()
