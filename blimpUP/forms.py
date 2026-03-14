from email.policy import default
from operator import mod
from django import forms
from .models import *

class RegisterForm(forms.ModelForm):
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'account_type')
    
    confirmation = forms.CharField(max_length=30)

class BlimpForm(forms.ModelForm):

    class Meta:
        model = Blimp
        exclude = ('owner', 'filled_capacity', 'status', 'average_rating')

class NoImageForm(forms.ModelForm):

    class Meta:
        model = Blimp
        exclude = ('owner', 'filled_capacity', 'status', 'image', 'average_rating')

class TripRequestForm(forms.Form):
    id = forms.IntegerField()
    username = forms.CharField()

    ACCEPT = "accept"
    DECLINE = "decline"
    CHOICES = [
        (ACCEPT, "accept"),
        (DECLINE, "decline"),
    ]
    choice = models.CharField(max_length=32, choices=CHOICES, default=ACCEPT)

class ReviewForm(forms.Form):
    RATINGS= [
    (0, 0),
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    ]
    rating = models.CharField(choices=RATINGS, default=5)
    comment = forms.CharField(max_length=300)