from django.contrib.auth.models import User
from django.db import models
from django_mysql.models import ListTextField



# UserProfile inherits the django User object, fields and methods on the User Profile are inherited
class UserProfile(User):
    image = models.ImageField(upload_to='images', blank=True)
    genderChoices = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=genderChoices)
    dob = models.DateField(max_length=8)
    # matches, likes and rejects are all ListTextFields with their base being CharField,
    # This list class is from the django_mysql library which allows lists. sqlite is still used as the database
    matches = ListTextField(
        base_field=models.CharField(max_length=150),
    )
    likes = ListTextField(
        base_field=models.CharField(max_length=150),
    )
    rejects = ListTextField(
        base_field=models.CharField(max_length=150),
    )

    def __str__(self):
          return "username: " + self.username + ", \nfirst name: " + self.first_name + ", \nlast name: " + self.last_name + ", \npassword: " + self.password + ", \nemail: " + self.email + ", \ndob: " + str(self.dob) + ", \ngender: " + self.gender + "fdg"

# hobby object contains the name and a many to many association with UserProfile
class Hobby(models.Model):
    hobbyName = models.CharField(max_length=100)
    # users is a many to many field. Many hobbies can have many UserProfiles and vice versa. This allows access to both
    users = models.ManyToManyField(UserProfile)

    def __str__(self):
        return self.hobbyName + " " + str(self.users)

# Message class containing the sender, recipient, messafe and timestamp
class Message(models.Model):
    # sender and recipient are many to one relationships to UserProfile, therefore the forigen key for sender
    # and recipient is the foreign key for the UserProfile
    sender = models.ForeignKey(UserProfile, related_name="sender",
        on_delete=models.CASCADE)

    recipient = models.ForeignKey(UserProfile, related_name="recipient",
        on_delete=models.CASCADE)
    message = models.CharField(max_length=200)
    timeStamp = models.DateTimeField()

    def __str__(self):
        return "sender: " +  str(self.sender.username) + ", recipient: " + str(self.recipient.username) + ", time: " + str(self.timeStamp) + ", message: " + str(self.message)
