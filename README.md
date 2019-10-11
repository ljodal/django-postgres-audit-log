# Django Postgres audit log

Audit logging for [Django](https://djangoproject.com) using Postgres triggers.


## Installation

```sh
pip install django-postgres-audit-log
```

## Usage

To get started auditing your models there are a few steps you need to complete:

1. Use this package's database wrapper:

   ```python
   # settings.py
   DATABASE = {
       'DEFAULT': {
           'engine': 'audit_log.db',
           ...
        },
   }
   ```

   This is required because this plugin relies on injecting extra SQL when you
   run migrations. If you already have a custom database wrapper or for some
   other reason cannot use this package's database wrapper you can include just
   the schema editor from `audit_log.db.schema_editor`.

2. Install the middleware

   ```python
   # settings.py
   MIDDLEWARE = [
       ...
       'audit_log.middleware.RequestContextMiddleware',
       ...
   ]
   ```

   In order to get details about the current request (like the current user)
   into the database we rely on a middleware that creates a temporary table and
   inserts information about the current request into that table. That table is
   read by the trigger to include the context in the audit log entries.

3. Decorate the models you want to audit log

   ```python
   # models.py
   from audit_log.decorators import audit_logged
   from django.db import models

   @audit_logged()
   class MyModel(models.Model):
       pass
   ``` 

   This decorator will dynamically create a model that includes all the fields
   from the base audit log model, plus a foreign key to the decorated model.
   You can access a model's audit log entries though `my_instance.audit_log`
   which will give you a normal QuerySet that you can filter as you like.


4. Make migrations

   ```sh
   ./manage.py makemigrations
   ```

   This will not create a migration for the audit log model of `MyModel`.

5. Migrate the database

   ```sh
   ./manage.py migrate
   ```

   This is where most of the magic happens. The schema editor of the custom
   database wrapper will pick up that we are migrating a model that is an audit
   log table for another model, and automagically install triggers on the table
   being audited to ensure that any change is picked up and logged.
