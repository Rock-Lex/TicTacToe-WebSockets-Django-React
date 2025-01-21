from django.utils.timezone import now


def get_current_timestamp():
    return now().strftime("%d.%m.%Y %H:%M:%S")