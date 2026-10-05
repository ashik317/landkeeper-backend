from django.db import migrations
from django.utils.text import slugify

INITIAL_CATEGORIES = [
    "Property Insurance Providers",
    "Broadband Providers",
    "Cleaning Services",
    "Gas Safety Certificate Providers",
    "Boiler Repair & Heating Services",
    "Mortgage Advisers",
    "Utility Providers",
]


def seed_categories(apps, schema_editor):
    MarketplaceCategory = apps.get_model("marketplace", "MarketplaceCategory")
    for order, name in enumerate(INITIAL_CATEGORIES, start=1):
        MarketplaceCategory.objects.get_or_create(
            name=name,
            defaults={"slug": slugify(name), "display_order": order},
        )


def unseed_categories(apps, schema_editor):
    MarketplaceCategory = apps.get_model("marketplace", "MarketplaceCategory")
    MarketplaceCategory.objects.filter(name__in=INITIAL_CATEGORIES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories, unseed_categories),
    ]
