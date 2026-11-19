"""Tests for customer repository persistence."""
import tempfile
import unittest
from pathlib import Path
from database import Database
from models.customer import Customer
from repositories.customer_repository import CustomerRepository
from exceptions import CustomerAlreadyExistsError


class CustomerRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.db')
        self.db.initialize()
        self.repo = CustomerRepository(self.db)
        self.customer = Customer('Ada Lovelace', 'ada@example.com', '08012345678')

    def tearDown(self):
        self.temp.cleanup()

    def test_save_and_get_by_id(self):
        self.repo.save(self.customer)
        self.assertEqual(self.repo.get_by_id(self.customer.customer_id), self.customer)

    def test_get_by_email(self):
        self.repo.save(self.customer)
        self.assertEqual(self.repo.get_by_email('ada@example.com').customer_id, self.customer.customer_id)

    def test_email_lookup_is_case_insensitive(self):
        self.repo.save(self.customer)
        self.assertIsNotNone(self.repo.get_by_email('ADA@EXAMPLE.COM'))

    def test_missing_customer_returns_none(self):
        self.assertIsNone(self.repo.get_by_id('missing'))

    def test_duplicate_email_is_rejected(self):
        self.repo.save(self.customer)
        with self.assertRaises(CustomerAlreadyExistsError):
            self.repo.save(Customer('Another Person', 'ADA@example.com'))

    def test_duplicate_id_is_rejected(self):
        self.repo.save(self.customer)
        duplicate = Customer('Another Person', 'other@example.com', customer_id=self.customer.customer_id)
        with self.assertRaises(CustomerAlreadyExistsError):
            self.repo.save(duplicate)

    def test_list_all(self):
        self.repo.save(self.customer)
        self.repo.save(Customer('Grace Hopper', 'grace@example.com'))
        self.assertEqual(len(self.repo.list_all()), 2)

    def test_exists_by_email(self):
        self.repo.save(self.customer)
        self.assertTrue(self.repo.exists_by_email('ada@example.com'))
        self.assertFalse(self.repo.exists_by_email('none@example.com'))

    def test_customer_survives_new_repository_instance(self):
        self.repo.save(self.customer)
        other = CustomerRepository(Database(self.db.path))
        self.assertIsNotNone(other.get_by_id(self.customer.customer_id))

    def test_timestamp_is_preserved(self):
        self.repo.save(self.customer)
        restored = self.repo.get_by_id(self.customer.customer_id)
        self.assertEqual(restored.created_at, self.customer.created_at)

    def test_phone_is_preserved(self):
        self.repo.save(self.customer)
        self.assertEqual(self.repo.get_by_id(self.customer.customer_id).phone, '08012345678')


if __name__ == '__main__':
    unittest.main()
