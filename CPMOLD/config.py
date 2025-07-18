

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///molds.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Local file storage - no cloud configuration needed

