from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0002_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.CharField(
                default='Не указан',
                help_text='Улица, дом, квартира, город',
                max_length=500,
                verbose_name='Адрес доставки',
            ),
            preserve_default=False,
        ),
    ]
