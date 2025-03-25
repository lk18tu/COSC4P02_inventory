from django.db import models

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """
        Automatically assign a category if not provided.
        """
        if not self.category or self.category.strip() == "":
            self.category = self.auto_assign_category()
        super().save(*args, **kwargs)

    def auto_assign_category(self):
        """
        Determine category based on predefined rules.
        """
        category_rules = {
            "Electronics": ["laptop", "monitor", "mouse", "keyboard", "printer"],
            "Furniture": ["desk", "chair", "table", "cabinet"],
            "Stationery": ["pen", "notebook", "eraser", "marker"],
            "Accessories": ["charger", "headphones", "usb", "adapter"]
        }

        lower_name = self.name.lower()

        for category, keywords in category_rules.items():
            if any(keyword in lower_name for keyword in keywords):
                return category
        
        return "Uncategorized"  # Default if no match found

    def __str__(self):
        return f"{self.name} ({self.category}) - {self.quantity}"

