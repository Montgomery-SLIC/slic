from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_sitecontent'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentationImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='documentation_images/')),
                ('original_filename', models.CharField(max_length=255)),
                ('uploaded_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='documentation_images',
                    to='accounts.user',
                )),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'documentation_images',
                'ordering': ['-uploaded_at'],
            },
        ),
    ]
