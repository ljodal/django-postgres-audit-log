# Django Postgres audit log

Audit logging for [Django](https://djangoproject.com) using Postgres triggers.


## Installation

This package is currently not published anywhere, so you have to install it
directly from GitHub:

```sh
pip install git+https://github.com/ljodal/django-postgres-audit-log.git
```

## Usage

To get started auditing your models there are a few steps you need to complete:

1. Use this package's database wrapper:

   ```python
   # settings.py
   DATABASE = {
       'DEFAULT': {
           'engine': 'audit_log.db.backend',
           ...
        },
   }
   ```

   This is highly recommended, but not strictly required. Doing this enables
   automatic audit logging registration for your models. It is also possible to
   use this library without using the custom database engine, but then you will
   have to manually enable audit logging on your models by using the provided
   migration operations.

   If you already have a custom database wrapper you can use or subclasss
   just the schema editor from `audit_log.db.backend.schema`.

2. Set up models for the audit logging, and add them to settings:

   ```python
   # my_app/models.py
   from audit_log.models import BaseContext, BaseLogEntry

   class AuditLogContext(BaseContext):
       class Meta:
           managed = False

   class AuditLogEntry(BaseLogEntry):
       pass
    ```

    ```python
    # settings.py

    AUDIT_LOG_CONTEXT_MODEL = 'my_app.AuditLogContext'
    AUDIT_LOG_ENTRY_MODEL = 'my_app.AuditLogEntry'
    ```

    You can also add fields to these models if you have additional context you
    want to include in the audit log. All fields from the context model are
    automatically copied to the log entries, so make sure to add any custom
    fields to both models.

    Also note that the context model is set as `managed = False`. That is
    important as that table should not exist in the database, instead that model
    is used to create a temporary table for each request etc.

3. Install the middleware

   ```python
   # settings.py
   MIDDLEWARE = [
       ...
       'audit_log.middleware.RequestContextMiddleware',
       ...
   ]
   ```

   In order to get details about the current request (like the current user)
   into the database we rely on a middleware that creates the temporary context
   table and inserts information about the current request into that table. That
   table is read by the trigger to include the context in the audit log entries.

4. Update the models you want to audit log

   ```python
   # models.py
   from audit_log.models import AuditLoggedModel

   class MyModel(AuditLoggedModel):
       pass
   ``` 

   Subclassing this model will add an `AuditLogsField` field to your model (this
   is virtual field that doesn't have a column in the database). It's a reverse
   lookup for the generic foreign key on `BaseLogEntry`, giving you easy access
   to audit log entries for that specific model and is also used by the schema
   editor to detect that triggers should be added to a certain model.


5. Make migrations

   ```sh
   ./manage.py makemigrations
   ```

   This will create migrations to add the `audit_logs` to each of the models you
   have updated to subclass `AuditLoggedModel`.

6. Migrate the database

   ```sh
   ./manage.py migrate
   ```

   This is where most of the magic happens. The schema editor of the custom
   database wrapper will pick up that we are migrating a model that has an
   `AuditLogsField` field and automagically install triggers on the table to
   ensure that any change is picked up and logged.
