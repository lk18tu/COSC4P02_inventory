# updateStock/tests.py

import uuid
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.utils import timezone
from inventoryApp.models import InvTable_Metadata
from updateStock.models import StockTransaction, StockUnit

User = get_user_model()


class StockTransactionModelTests(TestCase):
    def setUp(self):
        self.meta = InvTable_Metadata.objects.create(table_name="test_table")
        self.tx = StockTransaction.objects.create(
            table_meta=self.meta,
            item_id=42,
            change=+5,
            tracking_id="unit-" + uuid.uuid4().hex
        )

    def test_str_shows_change_and_tracking(self):
        sign = "+" if self.tx.change > 0 else ""
        expected = (
            f"{self.meta.table_name}•{self.tx.item_id} "
            f"{sign}{self.tx.change} (unit={self.tx.tracking_id})"
        )
        self.assertEqual(str(self.tx), expected)

    def test_transaction_timestamp_auto_now(self):
        now = timezone.now()
        delta = now - self.tx.created_at
        self.assertTrue(0 <= delta.total_seconds() < 5)


class StockUnitModelTests(TestCase):
    def setUp(self):
        self.meta = InvTable_Metadata.objects.create(table_name="test_table")
        self.unit = StockUnit.objects.create(
            table_meta=self.meta,
            item_id=7,
            tracking_id="unit-alpha",
            status="In Stock",
            location="Back Room"
        )

    def test_unit_str(self):
        expected = f"{self.unit.tracking_id} ({self.unit.status}@{self.unit.location})"
        self.assertEqual(str(self.unit), expected)


class UpdateStockViewTests(TestCase):
    def setUp(self):
        # create & log in a user
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.force_login(self.user)

        # create a meta record
        self.meta = InvTable_Metadata.objects.create(table_name="test_table")

        # ——— create a real SQL table named test_table with the expected columns ———
        with connection.cursor() as c:
            c.execute("""
                CREATE TABLE `test_table` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255)           NOT NULL,
                    quantity_stock INT           NOT NULL DEFAULT 0,
                    reorder_level   INT           NOT NULL DEFAULT 0
                );
            """)
            # insert one dummy row (id=1)
            c.execute("""
                INSERT INTO `test_table` (title, quantity_stock, reorder_level)
                     VALUES ('Dummy Item', 0, 0);
            """)

        # prep one StockUnit so we can test removal
        StockUnit.objects.create(
            table_meta=self.meta,
            item_id=1,
            tracking_id="unit-to-remove"
        )

        # our “tenant” placeholder in the URL
        self.tenant = self.meta.table_name

    def tearDown(self):
        # drop the temporary SQL table after each test
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS `test_table`;")

    def test_add_stock_endpoint_creates_transaction(self):
        url = f"/{self.tenant}/updateStock/products/{self.meta.table_name}/1/add/"
        resp = self.client.post(
            url,
            {"tracking_id": "new-unit", "amount": "1"},
            follow=True
        )
        self.assertEqual(resp.status_code, 200)

        # verify a +1 StockTransaction was created
        tx = StockTransaction.objects.get(
            table_meta=self.meta,
            item_id=1,
            tracking_id="new-unit"
        )
        self.assertEqual(tx.change, 1)

        # and that a StockUnit was also created
        unit = StockUnit.objects.get(tracking_id="new-unit")
        self.assertEqual(unit.table_meta, self.meta)
        self.assertEqual(unit.status, "In Stock")

    def test_remove_stock_endpoint_marks_unit_removed(self):
        url = f"/{self.tenant}/updateStock/products/{self.meta.table_name}/1/remove/"
        resp = self.client.post(
            url,
            {"tracking_id": "unit-to-remove", "amount": "1"},
            follow=True
        )
        self.assertEqual(resp.status_code, 200)

        # the existing unit’s status should now be “Removed”
        unit = StockUnit.objects.get(tracking_id="unit-to-remove")
        self.assertEqual(unit.status, "Removed")
