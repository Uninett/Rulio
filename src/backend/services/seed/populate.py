from django.db import transaction

from backend.services.seed.seed_addresses import seed_addresses
from backend.services.seed.seed_services import seed_services


@transaction.atomic
def populate_db():
    seed_addresses()
    seed_services()