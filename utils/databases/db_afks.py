from . import afks_database, GetDoc

from umongo.fields import *
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance as Instance
from umongo.frameworks.motor_asyncio import MotorAsyncIODocument as Document

instance = Instance(afks_database)


@instance.register
class AFK(Document, GetDoc):
    id = IntField(attribute='_id', required=True)
    reason = StrField(default=None)
    date = DateTimeField(default=None)

    is_afk = BooleanField(default=False)
    default = StrField(default=None)

    class Meta:
        collection_name = 'AFKs'