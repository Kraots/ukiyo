from . import giveaways_database, GetDoc

from umongo.fields import *
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance as Instance
from umongo.frameworks.motor_asyncio import MotorAsyncIODocument as Document

instance = Instance(giveaways_database)


@instance.register
class Giveaway(Document, GetDoc):
    id = IntField(attribute='_id', required=True)
    prize = StrField(required=True)
    expire_date = DateTimeField(required=True)

    participants = ListField(IntField(), default=[])
    messages_requirement = IntField(default=0)

    class Meta:
        collection_name = 'Giveaways'