from . import mutes_database, GetDoc

from umongo.fields import *
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance as Instance
from umongo.frameworks.motor_asyncio import MotorAsyncIODocument as Document

instance = Instance(mutes_database)


@instance.register
class Mute(Document, GetDoc):
    id = IntField(attribute='_id', required=True)
    muted_by = IntField(required=True)
    muted_until = DateTimeField(required=True)
    reason = StrField(required=True)
    duration = StrField(required=True)

    streak = IntField(default=0)
    streak_expire_date = DateTimeField()
    permanent = BoolField(default=False)
    is_muted = BoolField(default=True)

    is_owner = BoolField(default=False)
    is_admin = BoolField(default=False)
    is_mod = BoolField(default=False)
    filter = BoolField(default=False)

    class Meta:
        collection_name = 'Mutes'