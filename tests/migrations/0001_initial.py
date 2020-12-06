# Generated by Django 3.1.4 on 2020-12-06 02:24

import audit_log.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLogContext',
            fields=[
                ('context_type', models.CharField(choices=[('HTTP request', 'http-request'), ('Management command', 'management-command'), ('Celery task', 'celery-task'), ('Test', 'test')], max_length=128, primary_key=True, serialize=False)),
                ('context', models.JSONField()),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuditLogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(null=True)),
                ('context_type', models.CharField(choices=[('HTTP request', 'http-request'), ('Management command', 'management-command'), ('Celery task', 'celery-task'), ('Test', 'test')], max_length=128)),
                ('context', models.JSONField()),
                ('action', models.CharField(choices=[('Insert', 'INSERT'), ('Update', 'UPDATE'), ('Delete', 'DELETE')], max_length=6)),
                ('at', models.DateTimeField()),
                ('changes', models.JSONField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('performed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MyConvertedToAuditLoggedModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('some_text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MyNonAuditLoggedModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('some_text', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='MyAuditLoggedModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('some_text', models.TextField()),
                ('audit_logs', audit_log.fields.AuditLogsField(to='tests.auditlogentry')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
