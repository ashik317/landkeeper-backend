from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("marketplace", "0002_seed_initial_categories"),
    ]

    operations = [
        migrations.AlterField(
            model_name="marketplacecategory",
            name="icon",
            field=models.TextField(blank=True, null=True, verbose_name="Icon"),
        ),
    ]
