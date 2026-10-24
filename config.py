import os


class Config:
    # Secret key used by Flask sessions and security features
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "test-nova-development-secret-key"
    )

    # SQLite database
    SQLALCHEMY_DATABASE_URI = "sqlite:///testnova.db"

    # Disable unnecessary SQLAlchemy event notifications
    SQLALCHEMY_TRACK_MODIFICATIONS = False