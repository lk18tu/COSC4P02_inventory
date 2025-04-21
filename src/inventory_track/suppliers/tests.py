from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Supplier

class SupplierModelTest(TestCase):
    def setUp(self):
        """Initialize test data"""
        self.supplier_data = {
            'name': 'Test Supplier',
            'email': 'test@supplier.com',
            'phone_number': '1234567890',
            'address': '123 Test Street'
        }
        self.supplier = Supplier.objects.create(**self.supplier_data)

    def test_create_supplier(self):
        """Test supplier creation"""
        self.assertEqual(self.supplier.name, self.supplier_data['name'])
        self.assertEqual(self.supplier.email, self.supplier_data['email'])
        self.assertEqual(self.supplier.phone_number, self.supplier_data['phone_number'])

    def test_update_supplier(self):
        """Test supplier update"""
        new_name = 'Updated Supplier'
        self.supplier.name = new_name
        self.supplier.save()
        updated_supplier = Supplier.objects.get(id=self.supplier.id)
        self.assertEqual(updated_supplier.name, new_name)

    def test_delete_supplier(self):
        """Test supplier deletion"""
        supplier_id = self.supplier.id
        self.supplier.delete()
        with self.assertRaises(Supplier.DoesNotExist):
            Supplier.objects.get(id=supplier_id)

    def test_supplier_str_method(self):
        """Test supplier string representation"""
        self.assertEqual(str(self.supplier), self.supplier_data['name'])

    def test_invalid_email_format(self):
        """Test email validation"""
        with self.assertRaises(ValidationError):
            invalid_supplier = Supplier(
                name='Invalid Email Supplier',
                email='invalid-email',
                phone_number='1234567890',
                address='789 Test Road'
            )
            invalid_supplier.full_clean()

    def test_blank_name(self):
        """Test name field required"""
        with self.assertRaises(ValidationError):
            invalid_supplier = Supplier(
                name='',
                email='blank@supplier.com',
                phone_number='1234567890',
                address='789 Test Road'
            )
            invalid_supplier.full_clean()