# Generated manually for Quote System
# Tarea 6: Sistema de Cotizaciones

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_service_alert_tables'),
    ]

    operations = [
        migrations.CreateModel(
            name='Quote',
            fields=[
                ('quote_id', models.AutoField(primary_key=True, serialize=False)),
                ('quote_number', models.CharField(max_length=20, unique=True)),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('SENT', 'Sent'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('EXPIRED', 'Expired'), ('CONVERTED', 'Converted to Work Order')], default='DRAFT', max_length=20)),
                ('quote_date', models.DateField()),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('subtotal', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('discount_percent', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('discount_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('tax_percent', models.DecimalField(decimal_places=2, default=Decimal('16.00'), max_digits=5)),
                ('tax_amount', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('total_hours', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=6)),
                ('currency_code', models.CharField(default='MXN', max_length=3)),
                ('notes', models.TextField(blank=True, null=True)),
                ('terms_and_conditions', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('client', models.ForeignKey(db_column='client_id', on_delete=django.db.models.deletion.CASCADE, to='core.client')),
                ('converted_to_wo', models.ForeignKey(blank=True, db_column='converted_to_wo_id', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='source_quote', to='core.workorder')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='quotes_created', to='auth.user')),
                ('equipment', models.ForeignKey(blank=True, db_column='equipment_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.equipment')),
            ],
            options={
                'db_table': 'svc.quotes',
                'ordering': ['-quote_date', '-quote_number'],
            },
        ),
        migrations.CreateModel(
            name='QuoteItem',
            fields=[
                ('quote_item_id', models.AutoField(primary_key=True, serialize=False)),
                ('service_code', models.CharField(blank=True, max_length=20, null=True)),
                ('description', models.TextField()),
                ('quantity', models.IntegerField(default=1)),
                ('hours', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5)),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=Decimal('500.00'), max_digits=10)),
                ('line_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=12)),
                ('notes', models.TextField(blank=True, null=True)),
                ('flat_rate', models.ForeignKey(blank=True, db_column='flat_rate_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.flatratestandard')),
                ('quote', models.ForeignKey(db_column='quote_id', on_delete=django.db.models.deletion.CASCADE, related_name='items', to='core.quote')),
            ],
            options={
                'db_table': 'svc.quote_items',
                'ordering': ['quote', 'quote_item_id'],
            },
        ),
        migrations.AddIndex(
            model_name='quote',
            index=models.Index(fields=['quote_number'], name='svc.quotes_quote_n_abc123_idx'),
        ),
        migrations.AddIndex(
            model_name='quote',
            index=models.Index(fields=['client', 'status'], name='svc.quotes_client__def456_idx'),
        ),
        migrations.AddIndex(
            model_name='quote',
            index=models.Index(fields=['quote_date', 'status'], name='svc.quotes_quote_d_ghi789_idx'),
        ),
    ]
