from flask_seeder import Seeder, Faker, generator
from random import randint
import requests
import os

class FullNameGenerator(generator.Generator):
    def generate(self):
        return generator.Name().generate()+' '+generator.Name().generate()

class DepartmentGenerator(generator.Generator):
    departments = ['IT', 'Managment', 'HR', 'PR']
    maxIndex = len(departments)-1
    def generate(self):
        randomIndex = randint(0, self.maxIndex)
        return self.departments[randomIndex]

class JobGenerator(generator.Generator):
    url = 'http://api.dataatwork.org/v1/jobs?limit=15'
    req = requests.get(url)
    jobs = [obj['title'] for obj in req.json()[:-1]]
    maxIndex = len(jobs) - 1
    def generate(self):
        randomIndex = randint(0, self.maxIndex)
        return self.jobs[randomIndex]

def generatePhoto(assistantID):
    url = 'https://thispersondoesnotexist.com/image'
    headers = {'User-Agent': 'My User Agent 1.0'}  # Doesn't work without custom User-Agent
    req = requests.get(url, headers=headers)
    response = req.content
    filePath = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)
        ),
        os.pardir,
        'uploads',
        f'{assistantID}.jpg'
    )
    with open(filePath, "wb") as f:
        f.write(response)

#flask seed run --root C:\Users\pc\Desktop\Bartek\projekty\flask\assistManager\seeds
class MySeeder(Seeder):
    def run(self):
        for model in self.db.Model._decl_class_registry.values():
            if hasattr(model, '__tablename__') and model.__tablename__ == "assistants":
                Assistant = model
        faker = Faker(
            cls=Assistant,
            init={
                'name': FullNameGenerator(),
                'department': DepartmentGenerator(),
                'job': JobGenerator(),
            }
        )
        assistants = [a for a in faker.create(3)]
        self.db.session.add_all(assistants)
        self.db.session.commit()
        for assistant in assistants:
            generatePhoto(assistant.id)