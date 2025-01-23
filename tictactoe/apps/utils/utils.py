import socket
from django.utils.timezone import now


def get_current_timestamp():
    return now().strftime("%d.%m.%Y %H:%M:%S")


def get_ipaddress():
   host_name = socket.gethostname()
   ip_address = socket.gethostbyname(host_name) 
   return "http://"+ip_address
