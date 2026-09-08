from typing import ClassVar

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies: ClassVar = [
        ("objects", "0005_tag_color"),
    ]

    operations: ClassVar = [
        migrations.AddConstraint(
            model_name="interface",
            constraint=models.UniqueConstraint(
                fields=("device", "name"),
                name="unique_interface_name_per_device",
            ),
        ),
    ]
