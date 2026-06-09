
from datetime import datetime

class VersionControl:
    def __init__(self, id:int, filter_id:int, datetime: datetime, tenant_id:int):
        self.id = id
        self.filter_id = filter_id
        self.datetime = datetime
        self.tenant_id = tenant_id