#!/bin/sh
set -e

echo "Waiting for database..."

python << EOF
import os
import time
import psycopg2

db_name = os.environ.get("DATABASE_NAME")
db_user = os.environ.get("DATABASE_USER")
db_password = os.environ.get("DATABASE_PASS")
db_host = os.environ.get("DATABASE_HOST", "db")
db_port = os.environ.get("DATABASE_PORT", "5432")

while True:
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        conn.close()
        print("Database is up.")
        break
    except psycopg2.OperationalError:
        print("Database unavailable, waiting 1 second...")
        time.sleep(1)
EOF

echo "Running migrations..."
python manage.py migrate --noinput


echo "Creating superuser if needed..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

if not username or not email or not password:
    print("Missing superuser environment variables, skipping.")
else:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("Superuser created.")
    else:
        print("Superuser already exists.")
EOF

echo "Creating default tenant if needed..."
python manage.py shell << EOF
from backend.objects.tenant_objects.tenant import Tenant

tenant, created = Tenant.objects.get_or_create(
    tenant_name="Global Tenant",
)

if not created:
    tenant.save()

print(f"Tenant ready: id={tenant.id}, name={tenant.tenant_name}, created={created}")
EOF

echo "Seeding database..."
python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
from backend.objects.tenant_objects.tenant import Tenant
from backend.services.seed.populate import populate_db

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
if not username:
    raise RuntimeError("DJANGO_SUPERUSER_USERNAME is not set.")

user = User.objects.get(username=username)
tenant = Tenant.objects.get(tenant_name="Global Tenant")

populate_db(actor=user, tenant_id=tenant.id)
print(f"Database seeded with actor={user.username}, tenant_id={tenant.id}, tenant_name={tenant.tenant_name}")
EOF
echo "Starting Django..."
exec python manage.py runserver 0.0.0.0:8000