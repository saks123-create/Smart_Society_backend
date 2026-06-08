import os
import unittest
from datetime import timedelta

os.environ.setdefault("SECRET_KEY", "test-secret-key")

from jose import jwt

from app.utils import security

class SecurityTests(unittest.TestCase):
    def test_password_hash_verifies_matching_password_only(self):
        hashed = security.get_password_hash("Resident@123")

        self.assertTrue(security.verify_password("Resident@123", hashed))
        self.assertFalse(security.verify_password("Wrong@123", hashed))

    def test_malformed_password_hash_is_treated_as_invalid(self):
        self.assertFalse(security.verify_password("Resident@123", "not-a-valid-hash"))

    def test_access_token_contains_access_type_and_subject(self):
        token = security.create_access_token(
            {"sub": "resident@example.com", "role": "resident"},
            expires_delta=timedelta(minutes=5),
        )

        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])

        self.assertEqual(payload["sub"], "resident@example.com")
        self.assertEqual(payload["role"], "resident")
        self.assertEqual(payload["token_type"], "access")

    def test_password_reset_decoder_rejects_email_verification_token(self):
        token = security.create_email_verification_token(
            user_id=7,
            email="resident@example.com",
            expires_delta=timedelta(minutes=5),
        )

        with self.assertRaisesRegex(ValueError, "Invalid reset token type"):
            security.decode_password_reset_token(token)


if __name__ == "__main__":
    unittest.main()
