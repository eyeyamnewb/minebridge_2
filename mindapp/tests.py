from django.test import TestCase
from decouple import config

bob = config("DEBUG")
print(bob)