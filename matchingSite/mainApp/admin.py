from django.contrib import admin
from .models import UserProfile, Hobby, Message

admin.site.register(UserProfile)
admin.site.register(Hobby)
admin.site.register(Message)
