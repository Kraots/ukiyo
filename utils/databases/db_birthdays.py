from . import birthdays_database, GetDoc

from umongo.fields import *
from umongo.frameworks.motor_asyncio import MotorAsyncIOInstance as Instance
from umongo.frameworks.motor_asyncio import MotorAsyncIODocument as Document

instance = Instance(birthdays_database)


@instance.register
class Birthday(Document, GetDoc):
    id = IntField(attribute='_id', required=True)

    timezone = StrField(required=True)
    birthday_date = DateTimeField(required=True)
    next_birthday = DateTimeField(required=True)

    class Meta:
        collection_name = 'Birthdays'