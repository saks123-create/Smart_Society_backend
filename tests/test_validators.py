import unittest

from app.schemas.validators import (
    validate_email,
    validate_name,
    validate_phone,
    validate_strong_password,
)
from app.utils.normalization import normalize_email


class ValidatorTests(unittest.TestCase):
    def test_normalize_email_trims_and_lowercases(self):
        self.assertEqual(normalize_email("  Resident@Example.COM  "), "resident@example.com")

    def test_validate_email_accepts_cleaned_lowercase_email(self):
        self.assertEqual(validate_email("  Admin@SmartSociety.COM "), "admin@smartsociety.com")

    def test_validate_phone_accepts_integer_and_returns_string(self):
        self.assertEqual(validate_phone(9876543210), "9876543210")

    def test_validate_phone_rejects_non_ten_digit_values(self):
        with self.assertRaisesRegex(ValueError, "10 digits"):
            validate_phone("98765")

    def test_validate_name_rejects_numbers_only(self):
        with self.assertRaisesRegex(ValueError, "cannot be numbers only"):
            validate_name("101")

    def test_validate_strong_password_requires_common_complexity_rules(self):
        self.assertEqual(validate_strong_password("Strong@123"), "Strong@123")
        with self.assertRaisesRegex(ValueError, "uppercase, lowercase, number"):
            validate_strong_password("weakpass")


if __name__ == "__main__":
    unittest.main()
