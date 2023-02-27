# V 0.0.3
# 2021-05-05

# Shell script to create a very simple Django Ninja project.
# This script require Python 3.x and pyenv
# Settings.py is config to Django 3.1.5 and Django Ninja 0.12.1

# The project contains:
# Settings config
# Admin config
# Create files api.py and schema.py used Django Ninja

# Download:

# git clone https://gist.github.com/6701a753ed4455ba1bc0013b99ddf17f.git /tmp/boilerplatesimpledjangoninja
# cp /tmp/boilerplatesimpledjangoninja/boilerplatesimpledjangoninja.sh .

# Usage:
# Type the following command, you can change the project name.

# source boilerplatesimpledjangoninja.sh myproject

# Colors
red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`

PROJECT=${1-myproject}

echo "${green}>>> The name of the project is '$PROJECT'.${reset}"

echo "${green}>>> Creating README.md${reset}"
cat << EOF > README.md
## This project was done with:

* Python 3.8.5
* Django 3.1.5
* Django Ninja 0.12.1
* Python Decouple 3.4

## How to run project?

* Clone this repository.
* Create virtualenv with Python 3.
* Active the virtualenv.
* Install dependences.
* Create .env run contrib/env_gen.py
* Run the migrations.

\`\`\`
git clone https://github.com/liviocunha/$PROJECT.git
cd $PROJECT
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 contrib/env_gen.py
python3 manage.py migrate
\`\`\`
EOF


echo "${green}>>> Creating virtualenv${reset}"
python3 -m venv .venv
echo "${green}>>> .venv is created${reset}"

# active
sleep 2
echo "${green}>>> activate the .venv${reset}"
source .venv/bin/activate
PS1="(`basename \"$VIRTUAL_ENV\"`)\e[1;34m:/\W\e[00m$ "
sleep 2

# install django, django ninja and others
echo "${green}>>> Installing the Django and Django Ninja${reset}"
pip install -U pip
pip install django==3.1.5 dj-database-url django-ninja==0.12.1 python-decouple
pip freeze > requirements.txt

# Create contrib/env_gen.py
echo "${green}>>> Creating the contrib/env_gen.py${reset}"
mkdir contrib
cat << EOF > contrib/env_gen.py
"""
Python SECRET_KEY generator.
"""
import random

chars = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
size = 50
secret_key = "".join(random.sample(chars, size))

chars = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ@#$%_"
size = 20
password = "".join(random.sample(chars, size))
CONFIG_STRING = """
DEBUG=True
SECRET_KEY=%s
ALLOWED_HOSTS=127.0.0.1, .localhost

#DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/NAME
#DB_NAME=
#DB_USER=
#DB_PASSWORD=%s
#DB_HOST=localhost

#DEFAULT_FROM_EMAIL=
#EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#EMAIL_HOST=
#EMAIL_PORT=
#EMAIL_HOST_USER=
#EMAIL_HOST_PASSWORD=
#EMAIL_USE_TLS=True
""".strip() % (secret_key, password)

# Writing our configuration file to '.env'
with open('.env', 'w') as configfile:
    configfile.write(CONFIG_STRING)

print('Success!')
print('Type: cat .env')
EOF

echo "${green}>>> Run contrib/env_gen.py${reset}"
python3 contrib/env_gen.py

echo "${green}>>> Creating .gitignore${reset}"
cat << EOF > .gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
#Pipfile.lock
# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/
.DS_Store
media/
staticfiles/
.ipynb_checkpoints/
EOF

# createproject
echo "${green}>>> Creating the project '$PROJECT' ...${reset}"
django-admin.py startproject $PROJECT .

echo "${green}>>> Creating the app 'core' ...${reset}"
python3 manage.py startapp core

# ********** EDITING FILES **********
echo "${green}>>> Editing settings.py${reset}"
# delete lines
gsed -i '23,28d' $PROJECT/settings.py

# write new lines
gsed -i '14i import os' $PROJECT/settings.py
gsed -i '15i from decouple import config, Csv' $PROJECT/settings.py
gsed -i '16i from dj_database_url import parse as dburl' $PROJECT/settings.py

gsed -i "25i SECRET_KEY = config('SECRET_KEY')\n" $PROJECT/settings.py

gsed -i "27i # SECURITY WARNING: don't run with debug turned on in production!" $PROJECT/settings.py
gsed -i "28i DEBUG = config('DEBUG', default=False, cast=bool)\n" $PROJECT/settings.py

gsed -i "30i ALLOWED_HOSTS = config('ALLOWED_HOSTS', default=[], cast=Csv())" $PROJECT/settings.py

gsed -i "43i \ \ \ \ 'core'," $PROJECT/settings.py

# delete lines
gsed -i '80,85d' $PROJECT/settings.py
# write new lines
gsed -i "80i default_dburl = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')" $PROJECT/settings.py
gsed -i "81i DATABASES = {" $PROJECT/settings.py
gsed -i "82i \ \ \ \ 'default': config('DATABASE_URL', default=default_dburl, cast=dburl)," $PROJECT/settings.py
gsed -i "83i \}" $PROJECT/settings.py


echo "STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')" >> $PROJECT/settings.py



# create files Django Ninja
echo "${green}>>> Creating core/schemas.py${reset}"
cat << EOF > core/schemas.py
from ninja import Schema
EOF

echo "${green}>>> Creating core/api.py${reset}"
cat << EOF > core/api.py
from django.shortcuts import get_object_or_404
from typing import List
from ninja import Router

router = Router()
EOF

echo "${green}>>> Editing urls.py${reset}"
cat << EOF > $PROJECT/urls.py
from django.urls import path
from django.contrib import admin
from ninja import NinjaAPI
from core.api import router as ${PROJECT}_router

api = NinjaAPI(
    version='1.0',
    csrf=True,
    title='Title API project',
    description='Description API project',
    urls_namespace='public_api',
)

api.add_router('/$PROJECT/', ${PROJECT}_router)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
]
EOF


# migrate
python3 manage.py makemigrations
python3 manage.py migrate

read -p "Create superuser? [Y/n] " answer
answer=${answer:-Y}
if [[ $answer == 'Y' || $answer == 'y' ]]; then
    echo "${green}>>> Creating a 'admin' user ...${reset}"
    echo "${green}>>> The password must contain at least 8 characters.${reset}"
    python3 manage.py createsuperuser --username='admin' --email=''
fi

echo "${red}>>> Important: Dont add .env in your public repository.${reset}"
echo "${red}>>> KEEP YOUR SECRET_KEY AND PASSWORDS IN SECRET!!!\n${reset}"
echo "${green}>>> Done${reset}"
echo "${red}>>> Finally, delete the boilerplatesimpledjangoninja.sh\n${reset}"
# https://www.gnu.org/software/sed/manual/sed.html
