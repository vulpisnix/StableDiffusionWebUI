from django.db.backends.signals import connection_created
from django.dispatch import receiver

has_initialized = False

@receiver(connection_created)
def after_db_connection(connection, **kwargs):
    global has_initialized
    if has_initialized: return
    has_initialized = True
    from web.sd_queue_thread import fetch_queue_from_db
    fetch_queue_from_db()