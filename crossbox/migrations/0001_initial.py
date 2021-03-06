# Generated by Django 3.0.8 on 2020-08-26 09:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CapacityLimit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minimum', models.IntegerField(verbose_name='Mínimo')),
                ('maximum', models.IntegerField(verbose_name='Máximo')),
                ('default', models.BooleanField(default=False, verbose_name='Predeterminado')),
            ],
            options={
                'verbose_name': 'Límite de Aforo',
                'verbose_name_plural': 'Límites de Aforo',
            },
        ),
        migrations.CreateModel(
            name='Day',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True, verbose_name='Día de la semana')),
                ('weekday', models.IntegerField(unique=True, verbose_name='Número de día de la semana (Lunes es 0)')),
            ],
            options={
                'verbose_name': 'Día',
            },
        ),
        migrations.CreateModel(
            name='Fee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_sessions', models.IntegerField(verbose_name='Número de sesiones')),
                ('price_cents', models.IntegerField(verbose_name='Precio en céntimos')),
                ('stripe_product_id', models.CharField(max_length=30, verbose_name='ID Producto Stripe')),
                ('stripe_price_id', models.CharField(max_length=30, verbose_name='ID Precio Stripe')),
                ('active', models.BooleanField(default=True, verbose_name='Activa')),
            ],
            options={
                'verbose_name': 'Cuota',
                'verbose_name_plural': 'Cuotas',
            },
        ),
        migrations.CreateModel(
            name='Hour',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hour', models.TimeField(unique=True, verbose_name='Hora de la sesión')),
            ],
            options={
                'verbose_name': 'Hora',
            },
        ),
        migrations.CreateModel(
            name='SessionType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Tipo de sesión')),
                ('default', models.BooleanField(default=False, verbose_name='Predeterminado')),
            ],
            options={
                'verbose_name': 'Tipo de Sesión',
                'verbose_name_plural': 'Tipos de Sesión',
            },
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250, unique=True, verbose_name='Pista')),
                ('default', models.BooleanField(default=False, verbose_name='Predeterminada')),
            ],
            options={
                'verbose_name': 'Pista',
                'verbose_name_plural': 'Pistas',
            },
        ),
        migrations.CreateModel(
            name='WeekTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Plantilla de semana')),
                ('default', models.BooleanField(default=False, verbose_name='Predeterminada')),
            ],
            options={
                'verbose_name': 'Plantilla de Semana',
                'verbose_name_plural': 'Plantillas de Semana',
            },
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wods', models.IntegerField(default=0)),
                ('stripe_customer_id', models.CharField(max_length=30, verbose_name='ID Cliente Stripe')),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=30, null=True, verbose_name='ID Subscripción Stripe')),
                ('stripe_subscription_price_item_id', models.CharField(blank=True, max_length=30, null=True, verbose_name='ID Precio de Subscripción Stripe')),
                ('stripe_next_payment_timestamp', models.IntegerField(blank=True, null=True, verbose_name='Timestamp próximo pago')),
                ('stipe_last_payment_timestamp', models.IntegerField(blank=True, null=True, verbose_name='Timestamp último pago')),
                ('fee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='subscribers', to='crossbox.Fee')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscriber', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Abonado',
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=True, verbose_name='Día')),
                ('capacity_limit', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crossbox.CapacityLimit')),
                ('hour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crossbox.Hour')),
                ('session_type', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='crossbox.SessionType')),
                ('track', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crossbox.Track')),
            ],
            options={
                'verbose_name': 'Sesión',
                'verbose_name_plural': 'Sesiones',
                'unique_together': {('date', 'hour', 'track')},
            },
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_digits', models.CharField(max_length=4, verbose_name='Últimos dígitos')),
                ('default', models.BooleanField(default=False, verbose_name='Por defecto')),
                ('stripe_card_id', models.CharField(max_length=40, verbose_name='ID Tarjeta Stripe')),
                ('subscriber', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='crossbox.Subscriber')),
            ],
            options={
                'verbose_name': 'Tarjeta',
                'verbose_name_plural': 'Tarjetas',
            },
        ),
        migrations.CreateModel(
            name='SessionTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('capacity_limit', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='crossbox.CapacityLimit')),
                ('day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crossbox.Day')),
                ('hour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crossbox.Hour')),
                ('week_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crossbox.WeekTemplate')),
            ],
            options={
                'verbose_name': 'Plantilla de Sesión',
                'verbose_name_plural': 'Plantillas de Sesión',
                'unique_together': {('day', 'hour', 'week_template')},
            },
        ),
        migrations.CreateModel(
            name='Reservation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='crossbox.Session')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reserva',
                'unique_together': {('user', 'session')},
            },
        ),
    ]
