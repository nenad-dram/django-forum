# django-forum

A simple forum application created with Django framework

## Initial startup

The application can be started via __start_env.sh__ file.
The script will create a venv, install required packages, initialize the DB and start the application server.  

## Usage

After the initial startup the application is available under *http://127.0.0.1:8000/forum/home*.

The following standard users are available: *john_doe (john.doe@mail.com), jane_doe (jane.doe@mail.com),
robert_brown (robert.brown@mail.com), mary_smith (mary.smith@mail.com)*, and the password for all of them is
*password*.  
The admin user has username *admin (admin@forum.com)* and password *admin*.

The application contains example threads in the following subcategories: Python, Java, Ping-pong, Linux, Idle.