#!/bin/bash

# create a virtual environment
python3 -m venv venv

# activate the virtual environment
source venv/bin/activate

# install packages
pip install -r requirements.txt

# create DB and tables
python manage.py migrate

# insert into DB
python manage.py loaddata init_user.json init_cat_subcat.json init_thread.json

# run the server
python manage.py runserver