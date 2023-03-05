## This project was done with:

- Python 3.8.5
- Django 3.1.5
- Django Ninja 0.12.1
- Python Decouple 3.4

## How to run project?

- Clone this repository.
- Create virtualenv with Python 3.
- Active the virtualenv.
- Install dependences.
- Create .env run contrib/env_gen.py
- Run the migrations.

```
git clone https://github.com/valmi-io/valmi_app_backend.git
cd valmi_app_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
#create .env file from .env-sample
python manage.py makemigrations **optional: delete existing  migrations and use this command to create fresh**
python manage.py migrate
python manage.py runserver 4000
```

```
To create admin user  from the venv
python manage.py shell
from core.models import User
user = User(username="adminUser", email="nag@valmi.io", is_superuser=True)
user.set_password()
user.save()
```
