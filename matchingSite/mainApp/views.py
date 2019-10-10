from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, QueryDict
import json
from urllib.parse import unquote
from .models import UserProfile, Hobby, Message
from django import forms
from django.contrib.auth.models import User
import datetime
from django.core.mail import EmailMessage
from django.db.models import Q


# Create your views here.


#index page defaults to log in page
def index(request):
    return render(request,'mainApp/login.html')


# logged in decorator, Checks if the user is logged in and returns the user in the session variable
# otherwise redirects to the login error page
def loggedin(view):
    def check_loggedin(request):
        if 'username' in request.session:
            username = request.session['username']
            user = UserProfile.objects.get(username=username)
            return view(request, user)
        else:
            return render(request,'mainApp/loginError.html')
    return check_loggedin


# checks if the username and password match/exist, if so adds to session variable
def login(request):
    #Get username and password entered by user from request body.
    username = request.POST['username']
    password = request.POST['password']

    # Checks to see if user exist and if password is correct.
    try:
        userToCheck = UserProfile.objects.get(username=username)
        if userToCheck.password == password:
            request.session['username'] = username
            request.session['password'] = password
            return JsonResponse({'message': 'Success', 'username': username, 'loggedin': True})
        else:
            return JsonResponse({'message':'Invalid username or password'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'message': "Invalid username or password"})

# when user logs out remove from session
def logout(request):
    request.session.flush()
    return render(request,'mainapp/login.html')

#if user tries to access a page which requires log in
def loginError(request):
    return render(request,'mainApp/login.html')

# opens the create account page
def createAccountOpen(request):
    return render(request, 'mainApp/createAccount.html')

#gets variables from request.POST and creates a new user, ensures username or email doesn't already exist
def createAccountSubmit(request):
    if UserProfile.objects.filter(username=request.POST.get('username')).exists():
        return render(request, 'mainApp/createAccount.html', {'Error': 'Username already exists'})
    if UserProfile.objects.filter(email=request.POST.get('email')).exists():
        return render(request, 'mainApp/createAccount.html', {'Error': 'Email already exists'})

    u = UserProfile(username = request.POST.get('username').strip(),
                    first_name = request.POST.get('first_name'),
                    last_name = request.POST.get('last_name'),
                    password = request.POST.get('password'),
                    email = request.POST.get('email').strip(),
                    dob = request.POST.get('dob'),
                    gender= request.POST.get('gender'))
    if request.FILES:
        img = request.FILES['imageInput']
    else:
        img = 'images/default-profile.png'
    u.image = img
    u.save()
    return render(request, 'mainApp/login.html')


# Opens the add hobbies page, gets the users current hobbies and hobbies they can add
@loggedin
def addHobbiesOpen(request, user):
    hobbyList = []
    currentHobbies = []
    current = Hobby.objects.filter(users=user)
    for hobby in current:
        currentHobbies.append(hobby.hobbyName)
    hobbyObj = Hobby.objects.all().values_list('hobbyName', flat=True)
    for name in hobbyObj:
        if name not in currentHobbies:
            hobbyList.append(name)
    return render(request, 'mainApp/addHobbies.html', {'hobbyList': hobbyList, 'currentHobbyList': currentHobbies})

# submit new hobbies to add or hobbies to remove
@loggedin
def addHobbiesSubmit(request, user):
    selectedHobbies = request.POST.getlist('hobbies')
    hobbiesToRemove = request.POST.getlist('hobbiesToRemove')
    for hobby in selectedHobbies:
        h = Hobby.objects.get(hobbyName=hobby)
        h.users.add(user)
        h.save()
    for hobby in hobbiesToRemove:
        h = Hobby.objects.get(hobbyName=hobby)
        h.users.remove(user)
        h.save()
    response = homePageOpen(request)
    return response

#function to get the age from the date of birth
def getAge(dob):
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

# gets the class of the age passed
def getAgeClass(age):
    if age < 18:
        return "under-18"
    elif age < 31:
        return "18-30"
    elif age < 41:
        return "31-40"
    elif age < 51:
        return "41-50"
    else:
        return "over-50"

# gets the list of users in the users matches list and adds new fields temporarily
def getUserListMatches(userQuerySet, user):
    userList = []
    for person in userQuerySet:
        if person.username in user.matches:
            person.age = getAge(person.dob)
            person.ageClass=getAgeClass(person.age)
            userList.append(person)
    return userList

# gets the list of users not in matches, searches, or likes and checks if other user likes them
def getUserListSearches(userQuerySet, user):
    userList = []
    for person in userQuerySet:
        if not(person.username in user.matches):
            if not(person.username in user.likes):
                if not(person.username in user.rejects):
                    person.age = getAge(person.dob)
                    person.ageClass=getAgeClass(person.age)
                    if user.username in person.likes:
                        person.likesYou = "wants to link"
                    userList.append(person)
    return userList

# gets list of users in the users likes list
def getUserListLikes(userQuerySet, user):
    userList = []
    for person in userQuerySet:
        if person.username in user.likes:
            person.age = getAge(person.dob)
            person.ageClass=getAgeClass(person.age)
            userList.append(person)
    return userList

# gets the list of hobbies other users have and calculates how many
# the user and them have in common, adds to a field
def getHobbyList(userList, myHobbyList):
    userHobbyList = []
    for person in userList:
        thisUserList = []
        thisUserList.append(person.username)
        for hobby in Hobby.objects.filter(users__username=person.username):
            thisUserList.append(hobby.hobbyName)
        userHobbyList.append(thisUserList)
        count = 0
        index = 0
        for thisHobby in thisUserList:
            if index is not 0 and thisHobby in myHobbyList:
                count += 1
            index += 1
        person.sameHobbiesCount = count
    return userHobbyList

# returns the hobbyName field from a list of Hobby objects
def myHobbyNames(myHobbies):
    myHobbyList = []
    for myhob in myHobbies:
        myHobbyList.append(myhob.hobbyName)
    return myHobbyList

# gets the user information into a dictionary, avoid repetition of code
def getUserContext(user):
    context = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'age': getAge(user.dob),
        'gender': user.gender,
        'image': user.image,
    }
    return context

# gets the list of matches the user has and sorts based on hobbies in common
@loggedin
def matches(request, user):
    myHobbies = Hobby.objects.filter(users__username=user.username)
    userQuerySet = UserProfile.objects.all().exclude(username=user.username)
    myHobbyList = myHobbyNames(myHobbies)
    userList = getUserListMatches(userQuerySet, user)
    userHobbyList = getHobbyList(userList, myHobbyList)
    userList = sorted(userList, reverse = True, key=lambda person: person.sameHobbiesCount)
    context = getUserContext(user)
    context['button'] = 'links'
    context['matchesList'] = userList
    context['hobbyList'] = userHobbyList
    context['description'] = 'Users you have matched with!'

    return render(request, 'mainApp/homePage.html', context)

# opens the searchs from home page
@loggedin
def homePageOpen(request, user):
    return searches(request)


# gets the list of searches the user has and sorts based on hobbies in common
@loggedin
def searches(request, user):
    myHobbies = Hobby.objects.filter(users__username=user.username)
    myHobbyList = myHobbyNames(myHobbies)
    userQuerySet = UserProfile.objects.all().exclude(username=user.username)
    userList = getUserListSearches(userQuerySet, user)
    userHobbyList = getHobbyList(userList, myHobbyList)
    userList = sorted(userList, reverse = True, key=lambda person: person.sameHobbiesCount)
    context = getUserContext(user)
    context['button'] = 'searches'
    context['searchList'] = userList
    context['hobbyList'] = userHobbyList
    context['description'] = 'Search for potential links'

    return render(request, 'mainApp/homePage.html', context)


# gets the list of likes the user has and sorts based on hobbies in common
@loggedin
def likes(request, user):
    myHobbies = Hobby.objects.filter(users__username=user.username)
    userQuerySet = UserProfile.objects.all().exclude(username=user.username)
    myHobbyList = myHobbyNames(myHobbies)
    userList = getUserListLikes(userQuerySet, user)
    userHobbyList = getHobbyList(userList, myHobbyList)
    userList = sorted(userList, reverse = True, key=lambda person: person.sameHobbiesCount)
    context = getUserContext(user)
    context['button'] = 'likes'
    context['likesList'] = userList
    context['hobbyList'] = userHobbyList
    context['description'] = 'Users you have requested to link with'

    return render(request, 'mainApp/homePage.html', context)

# opens edit account details with the fields filled
@loggedin
def editAccountDetails(request, user):
	return render(request, 'mainApp/editAccountDetails.html', getUserContext(user))

# gets the fields to from the edit account form and changes the UserProfile object
@loggedin
def editAccountSubmit(request, user):
    p = UserProfile.objects.get(username = user.username)
    password = request.POST['password']
    if p.password == password:
        p.first_name = request.POST['first_name']
        p.last_name = request.POST['last_name']
        p.email = request.POST['email'].strip()
        p.dob = request.POST['dob']
        p.gender = request.POST['gender']
        p.save();
        return JsonResponse({'message': 'Success','loggedin': True})
    elif p.password != password:
        return JsonResponse({'message':'Incorrect Password'})
    else:
        return JsonResponse({'message':'Error saving changes'})

# opens the edit password page
@loggedin
def editAccountPassword(request, user):
    return render(request, 'mainApp/editAccountPassword.html')

# changes the users password with validatin checks
@loggedin
def editAccountPasswordSubmit(request, user):
    p = UserProfile.objects.get(username = user.username)
    password = request.POST['password']
    newPassword = request.POST['newPassword']
    reNewPassword = request.POST['reNewPassword']
    if p.password == password and newPassword==reNewPassword:
        p.password = newPassword
        p.save();
        return JsonResponse({'message': 'Success','loggedin': True})
    elif p.password != password:
        return JsonResponse({'message':'Wrong Password'})
    elif newPassword != reNewPassword:
        return JsonResponse({'message':'New password doesnt match'})

# checks if the user likes or rejects someone and if it was on matches, likes, or getUserListSearches
# if there was a like, an email is sent to the person being liked
# if there is a match, the user and the other person receice an email
@loggedin
def likeOrReject(request, user):
    theirUsername = request.POST['theirUsername']
    them = UserProfile.objects.get(username=theirUsername)
    action = request.POST['action']
    type = request.POST['type']
    email = them.email
    if action == "like":
        if user.username in them.likes:
            user.matches.append(theirUsername)
            them.matches.append(user.username)
            them.likes.remove(user.username)
            if theirUsername in  user.likes:
                user.likes.remove(theirUsername)
            body = "Hi "+ them.first_name+"\n" + "You have matched " + user.first_name
            email = EmailMessage('LetsLink new match', body, to=[email])
            email.send()
            body = "Hi "+ user.first_name+"\n" + "You have matched " + them.first_name
            email = EmailMessage('LetsLink new match', body, to=[user.email])
            email.send()
        else:
            user.likes.append(theirUsername)
            body = "Hi "+ them.first_name+"\n" + "You have received a like from " + user.first_name
            email = EmailMessage('LetsLink new like', body, to=[email])
            email.send()

    elif action == "reject":
        user.rejects.append(theirUsername)
        them.rejects.append(user.username)
        if theirUsername in user.likes:
            user.likes.remove(theirUsername)
        if user.username in them.likes:
            them.likes.remove(user.username)
        if theirUsername in user.matches:
            user.matches.remove(theirUsername)
        if user.username in them.matches:
            them.matches.remove(user.username)

    user.save()
    them.save()
    return JsonResponse({'message': 'success'})


# edits the users photo
@loggedin
def editPhoto(request, user):
    if request.FILES:
        img = request.FILES['imageInput']
    user.image = img
    user.save();
    return matches(request)


# opesn the chat page and gets the matches which the user can chat to
@loggedin
def openChats(request, user):
    userQuerySet = UserProfile.objects.all().exclude(username=user.username)
    userList = []
    for person in userQuerySet:
        if person.username in user.matches:
            userList.append(person)
    if len(userList) >=1:
        firstPerson = userList[0].username
    else:
        firstPerson= ""

    context = getUserContext(user)
    context['matchesList'] = userList
    context['firstPerson'] = firstPerson

    return render(request, 'mainApp/chats.html', context)

# gets the list of messages which contain the user and the sender or recipient
# the list is this sorted by time and split based on who was the sender and recipient
def getSenderAndRecipientMessages(user, r):
    thisChat = Message.objects.filter(Q(Q(sender=user) & Q(recipient= r)) | Q(Q(sender=r) & Q(recipient=user)))
    messageList = []
    for thisMessage in thisChat:
        messageList.append((thisMessage.message, thisMessage.sender.username, thisMessage.recipient.username, thisMessage.timeStamp,thisMessage.sender.image, thisMessage.recipient.image))
    sortedList = sorted(messageList, key=lambda tuple: tuple[3])
    newList = []
    for tupleMessage in sortedList:
        newList.append(str(tupleMessage[0])+";"+str(tupleMessage[1]) +";"+str(tupleMessage[2])+";"+str(tupleMessage[3])+";"+str(tupleMessage[4])+";"+str(tupleMessage[5]))
    context = {
        'messageList': newList,
        'theirUsername': r.username,
        'username': user.username
    }
    return context

# gets sender and recipient and calls function to get messages
@loggedin
def getMessages(request, user):
    them = request.GET['them']
    r = UserProfile.objects.get(username=them)
    return JsonResponse(getSenderAndRecipientMessages(user, r))


# adds a new message and returns a new list of messages for this user and recipient
@loggedin
def addMessage(request, user):
    them = request.POST.get('them')
    r = UserProfile.objects.get(username=them)
    message = request.POST.get('message').replace(";", ",")
    time = datetime.datetime.now()
    m = Message(sender=user, recipient= r, message = message, timeStamp = time)
    m.save()
    return JsonResponse(getSenderAndRecipientMessages(user, r))


# opens the profile page of the intended user
@loggedin
def openProfile(request, user):
    them = UserProfile.objects.get(username=request.GET['them'])
    theirHobbies = Hobby.objects.filter(users__username=them.username)
    context = getUserContext(them)
    context['theirHobbies'] = myHobbyNames(theirHobbies)

    return render(request, 'mainApp/profile.html', context)
