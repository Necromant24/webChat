from peewee import *


db = SqliteDatabase('people.db')

class Person(Model):
    name = CharField()
    age=IntegerField()
    event=TextField()
    birthday = DateField()
    id = IntegerField(primary_key=True)

    class Meta:
        database = db


db.connect()

db.create_tables([Person])

def getUserList():
    cursor = db.execute_sql('SELECT name,id FROM users')


print(getUserList())



