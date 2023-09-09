from . import intros_database, GetDoc

from umongo.fields import *
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance as Instance
from umongo.frameworks.motor_asyncio import MotorAsyncIODocument as Document

instance = Instance(intros_database)


@instance.register
class Intros(Document, GetDoc):
    id = IntField(attribute='_id', required=True)
    
    name = StrField(required=True)
    age = IntField(required=True)
    pronouns = StrField(required=True)
    gender = StrField(required=True)
    sexuality = StrField(required=True)
    country = StrField(required=True)
    dms = StrField(required=True)
    likes = StrField(required=True)
    dislikes = StrField(required=True)
    hobbies = StrField(required=True)

    message_id = IntField(required=True)
    jump_url = StrField(required=True)
    created_at = DateTimeField(required=True)

    class Meta:
        collection_name = 'Intros'