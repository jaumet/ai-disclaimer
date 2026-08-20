from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("projects", "0005_adhesion")]

    operations = [
        migrations.AddField(model_name="adhesion", name="comment", field=models.TextField(blank=True, max_length=600)),
        migrations.AddField(model_name="adhesion", name="comment_status", field=models.CharField(choices=[("clean", "OK"), ("needs_review", "NEEDS REVIEW")], default="clean", max_length=20)),
        migrations.AddField(model_name="adhesion", name="comment_review_reason", field=models.CharField(blank=True, max_length=120)),
    ]
