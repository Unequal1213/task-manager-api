import os
import secrets
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status

from app.api.auth import login
from app.core.jwt import decode_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest


class LoginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.credentials = LoginRequest(
            email="login_user@example.com",
            password="StrongPassword123!",
        )
        self.user = User(
            id=42,
            username="login_user",
            email=self.credentials.email,
            password_hash="$argon2id$stored-hash",
        )
        self.jwt_environment = {
            "JWT_SECRET_KEY": secrets.token_hex(32),
            "JWT_ALGORITHM": "HS256",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        }

    @patch("app.api.auth.verify_password", return_value=True)
    def test_login_returns_access_token(
        self,
        mock_verify_password: MagicMock,
    ) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = self.user

        with patch.dict(os.environ, self.jwt_environment):
            response = login(self.credentials, db)
            payload = decode_access_token(response.access_token)

        mock_verify_password.assert_called_once_with(
            self.credentials.password,
            self.user.password_hash,
        )
        self.assertEqual(response.token_type, "bearer")
        self.assertEqual(payload["sub"], str(self.user.id))

    @patch("app.api.auth.create_access_token")
    @patch("app.api.auth.verify_password", return_value=False)
    def test_login_rejects_incorrect_password(
        self,
        mock_verify_password: MagicMock,
        mock_create_access_token: MagicMock,
    ) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = self.user

        with self.assertRaises(HTTPException) as context:
            login(self.credentials, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            context.exception.detail,
            "Invalid email or password",
        )
        mock_verify_password.assert_called_once()
        mock_create_access_token.assert_not_called()

    @patch("app.api.auth.create_access_token")
    @patch("app.api.auth.verify_password")
    def test_login_rejects_unknown_email(
        self,
        mock_verify_password: MagicMock,
        mock_create_access_token: MagicMock,
    ) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(HTTPException) as context:
            login(self.credentials, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.assertEqual(
            context.exception.detail,
            "Invalid email or password",
        )
        mock_verify_password.assert_not_called()
        mock_create_access_token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
