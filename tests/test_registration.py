import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status

from app.api.auth import register
from app.schemas.user import UserCreate


class RegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = UserCreate(
            username="swagger_user",
            email="swagger_user@example.com",
            password="StrongPassword123!",
        )

    @patch("app.api.auth.hash_password")
    def test_register_creates_user_with_hashed_password(
        self,
        mock_hash_password: MagicMock,
    ) -> None:
        mock_hash_password.return_value = "$argon2id$test-hash"
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [None, None]

        response = register(self.user, db)

        mock_hash_password.assert_called_once_with(self.user.password)
        created_user = db.add.call_args.args[0]
        self.assertEqual(created_user.password_hash, "$argon2id$test-hash")
        self.assertNotEqual(created_user.password_hash, self.user.password)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(created_user)
        self.assertEqual(response["username"], self.user.username)
        self.assertEqual(response["email"], self.user.email)

    @patch("app.api.auth.hash_password")
    def test_register_rejects_duplicate_email(
        self,
        mock_hash_password: MagicMock,
    ) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()

        with self.assertRaises(HTTPException) as context:
            register(self.user, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            context.exception.detail,
            "A user with this email already exists",
        )
        mock_hash_password.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_not_called()

    @patch("app.api.auth.hash_password")
    def test_register_rejects_duplicate_username(
        self,
        mock_hash_password: MagicMock,
    ) -> None:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [
            None,
            MagicMock(),
        ]

        with self.assertRaises(HTTPException) as context:
            register(self.user, db)

        self.assertEqual(
            context.exception.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            context.exception.detail,
            "A user with this username already exists",
        )
        mock_hash_password.assert_not_called()
        db.add.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
