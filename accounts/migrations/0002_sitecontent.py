from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('content', models.TextField(blank=True, default='')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'site_contents',
            },
        ),
    ]
