from django.db import migrations, models


def create_badge_configuration_metric(apps, schema_editor):
    SiteMetric = apps.get_model("projects", "SiteMetric")
    SiteMetric.objects.create(key="badge_configurations", value=123)


class Migration(migrations.Migration):
    dependencies = [("projects", "0007_remove_magiclink_user_and_more")]
    operations = [
        migrations.CreateModel(
            name="SiteMetric",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=50, unique=True)),
                ("value", models.PositiveBigIntegerField(default=0)),
            ],
        ),
        migrations.RunPython(create_badge_configuration_metric, migrations.RunPython.noop),
    ]
