import os
import secrets
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.api.auth import read_current_user
from app.api.dependencies import get_current_user
from app.core.jwt import create_access_token
from app.models.user import User
from app.schemas.user import UserResponse


class CurrentUserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.jwt_environment = {
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "JWT_ALGORITHM": "HS256",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        }
        self.environment_patch = unittest.mock.patch.dict(
            os.environ,
            self.jwt_environment,
        )
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)

        self.user = User(
            id=42,
            username="current_user",
            email="current_user@example.com",
            password_hash="$argon2id$stored-hash",
            created_at=datetime.now(timezone.utc),
        )

    def test_get_current_user_accepts_valid_token(self) -> None:
        token = create_access_token(subject=str(self.user.id))
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = self.user

        current_user = get_current_user(credentials, db)
        response = UserResponse.model_validate(
            read_current_user(current_user)
        )

        self.assertEqual(current_user, self.user)
        self.assertEqual(response.id, self.user.id)
        self.assertNotIn("password_hash", response.model_dump())

    def test_get_current_user_rejects_invalid_token(self) -> None:
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token",
        )
        db = MagicMock()

        self._assert_unauthorized(credentials, db)
        db.query.assert_not_called()

    def test_get_current_user_rejects_missing_token(self) -> None:
        db = MagicMock()

        self._assert_unauthorized(None, db)
        db.query.assert_not_called()

    def test_get_current_user_rejects_expired_token(self) -> None:
        token = jwt.encode(
            {
                "sub": str(self.user.id),
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            self.jwt_environment["JWT_SECRET_KEY"],
            algorithm=self.jwt_environment["JWT_ALGORITHM"],
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )
        db = MagicMock()

        self._assert_unauthorized(credentials, db)
        db.query.assert_not_called()

    def test_get_current_user_rejects_missing_user(self) -> None:
        token = create_access_token(subject=str(self.user.id))
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        self._assert_unauthorized(credentials, db)

    def _assert_unauthorized(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        db: MagicMock,
    ) -> None:
        with self.assertRaises(HTTPException) as context:
            get_current_user(credentials, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            context.exception.detail,
            "Could not validate credentials",
        )
        self.assertEqual(
            context.exception.headers,
            {"WWW-Authenticate": "Bearer"},
        )


if __name__ == "__main__":
    unittest.main()
