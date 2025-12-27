import os
import motor.motor_asyncio

key1 = os.getenv('MONGODBLEVELSKEY')
cluster1 = motor.motor_asyncio.AsyncIOMotorClient(key1)
levels_database = cluster1['Ukiyo']  # Levels

key2 = os.getenv('MONGODBMUTESKEY')
cluster2 = motor.motor_asyncio.AsyncIOMotorClient(key2)
mutes_database = cluster2['Ukiyo']  # Mutes

key3 = os.getenv('MONGODBMARRIAGESKEY')
cluster3 = motor.motor_asyncio.AsyncIOMotorClient(key3)
marriages_database = cluster3['Ukiyo']  # Marriages

key4 = os.getenv('MONGODBMISCKEY')
cluster4 = motor.motor_asyncio.AsyncIOMotorClient(key4)
misc_database = cluster4['Ukiyo']  # Misc

key6 = os.getenv('MONGODBINTROSKEY')
cluster6 = motor.motor_asyncio.AsyncIOMotorClient(key6)
intros_database = cluster6['Ukiyo']  # Intros

key7 = os.getenv('MONGODBBIRTHDAYSKEY')
cluster7 = motor.motor_asyncio.AsyncIOMotorClient(key7)
birthdays_database = cluster7['Ukiyo']  # Birthdays

key8 = os.getenv('MONGODBAFKSKEY')
cluster8 = motor.motor_asyncio.AsyncIOMotorClient(key8)
afks_database = cluster8['Ukiyo']  # AFKS

key9 = os.getenv('MONGODBGIVEAWAYSKEY')
cluster9 = motor.motor_asyncio.AsyncIOMotorClient(key9)
giveaways_database = cluster9['Ukiyo']  # Giveaways