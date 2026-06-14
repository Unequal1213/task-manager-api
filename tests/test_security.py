import unittest

from app.core.security import hash_password, verify_password


class PasswordSecurityTests(unittest.TestCase):
    def test_hash_password_creates_verifiable_argon2_hash(self) -> None:
        plain_password = "StrongPassword123!"

        hashed_password = hash_password(plain_password)

        self.assertNotEqual(hashed_password, plain_password)
        self.assertTrue(hashed_password.startswith("$argon2"))
        self.assertTrue(verify_password(plain_password, hashed_password))
        self.assertFalse(verify_password("WrongPassword123!", hashed_password))


if __name__ == "__main__":
    unittest.main()
