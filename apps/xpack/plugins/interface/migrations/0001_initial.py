# -*- coding: utf-8 -*-
#
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Interface',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo_logout', models.CharField(default='/static/img/logo.png', max_length=1024, verbose_name='Logo')),
                ('logo_index', models.CharField(default='/static/img/logo_text_white.png', max_length=1024, verbose_name='Logo index')),
                ('login_image', models.CharField(default='/static/img/login_image.png', max_length=1024, verbose_name='Login image')),
                ('favicon', models.CharField(default='/static/img/facio.ico', max_length=1024, verbose_name='Favicon')),
                ('login_title', models.CharField(default='JumpServer 开源堡垒机', max_length=1024, verbose_name='Login title')),
                ('theme', models.CharField(default='classic_green', max_length=128, verbose_name='Theme')),
                ('theme_info', models.JSONField(default=dict, verbose_name='Theme info')),
                ('footer_content', models.TextField(blank=True, default='', verbose_name='Footer content')),
            ],
            options={
                'verbose_name': 'Interface setting',
                'db_table': 'xpack_interface',
            },
        ),
    ]

