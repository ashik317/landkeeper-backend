from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('property', '0005_uploaddocument_organisation'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS property_mortgage_mortgage_documents;",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
