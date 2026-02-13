# Generated manually for Service Alert System improvements
# Tarea 5.3: Sistema de Alertas - Mejoras avanzadas

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_extend_oem_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceAlertThreshold',
            fields=[
                ('threshold_id', models.AutoField(primary_key=True, serialize=False)),
                ('threshold_key', models.CharField(max_length=50, unique=True)),
                ('threshold_name', models.CharField(max_length=100)),
                ('value', models.FloatField(help_text='Threshold value')),
                ('unit', models.CharField(blank=True, help_text='Unit of measurement (e.g., hours, %, count)', max_length=20, null=True)),
                ('category', models.CharField(default='general', help_text='Category: orders, technicians, inventory, etc.', max_length=50)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'db_table': 'app.service_alert_thresholds',
                'ordering': ['category', 'threshold_key'],
            },
        ),
        migrations.CreateModel(
            name='ServiceAlertEscalation',
            fields=[
                ('escalation_id', models.AutoField(primary_key=True, serialize=False)),
                ('alert_id', models.IntegerField(help_text='Reference to app.alerts.alert_id')),
                ('original_severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=10)),
                ('escalated_severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=10)),
                ('escalation_level', models.IntegerField(default=1, help_text='Number of times this alert has been escalated')),
                ('escalated_at', models.DateTimeField(auto_now_add=True)),
                ('escalated_by', models.IntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'app.service_alert_escalations',
                'ordering': ['-escalated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='servicealertthreshold',
            index=models.Index(fields=['threshold_key', 'is_active'], name='app.service_thresh_e8d1f2_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealertthreshold',
            index=models.Index(fields=['category'], name='app.service_thresh_9c3f4a_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealertescalation',
            index=models.Index(fields=['alert_id', 'escalated_at'], name='app.service_escalat_2d5e8b_idx'),
        ),
        migrations.AddIndex(
            model_name='servicealertescalation',
            index=models.Index(fields=['escalation_level'], name='app.service_escalat_5a7f6c_idx'),
        ),
    ]
