# Generated by Django 5.1 on 2024-08-21 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_movementlog_action_type_alter_movementlog_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='movementlog',
            name='observation',
            field=models.TextField(blank=True, null=True),
        ),
    ]
