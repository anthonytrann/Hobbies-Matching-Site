from django.urls import path
from mainApp import views

# A list is url paths which, when entered, call the corrosponding method in views.py
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('createAccount/', views.createAccountOpen, name='createAccount'),
    path('createAccountSubmit/', views.createAccountSubmit, name='createAccountSubmit'),
    path('homePage/', views.homePageOpen, name='homePageOpen'),
    path('logout/', views.logout, name='logout'),
    path('addHobbies/', views.addHobbiesOpen, name='addHobbies'),
    path('addHobbiesSubmit/', views.addHobbiesSubmit, name='addHobbiesSubmit'),
    path('loginError/', views.loginError, name='loginError'),
    path('matches/', views.matches, name='matches'),
    path('searches/', views.searches, name='searches'),
    path('likes/', views.likes, name='likes'),
    path('editAccountDetails/', views.editAccountDetails, name='editAccountDetails'),
    path('editAccountSubmit/', views.editAccountSubmit, name='editAccountSubmit'),
    path('editAccountPassword/', views.editAccountPassword, name='editAccountPassword'),
    path('editAccountPasswordSubmit/', views.editAccountPasswordSubmit, name='editAccountPasswordSubmit'),
    path('likeOrReject/', views.likeOrReject, name='likeOrReject'),
    path('editPhoto/', views.editPhoto, name='editPhoto'),
    path('openChats/', views.openChats, name='openChats'),
    path('getMessages/', views.getMessages, name='getMessages'),
    path('addMessage/', views.addMessage, name='addMessage'),
    path('openProfile/', views.openProfile, name='openProfile')
]
