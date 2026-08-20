from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0004_magiclink_code_hash")]

    operations = [
        migrations.CreateModel(
            name="Adhesion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("supporter_type", models.CharField(choices=[("person", "A person"), ("organization", "An organization")], default="person", max_length=20)),
                ("organization_name", models.CharField(blank=True, max_length=160)),
                ("display_publicly", models.BooleanField(default=True)),
                ("pledge_version", models.CharField(default="1.0", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
