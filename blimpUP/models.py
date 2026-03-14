from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.deletion import CASCADE, SET_NULL
import uuid

class User(AbstractUser):
    PASSENGER = "passenger"
    OWNER = "owner"
    ACCOUNT_TYPE = [
        (PASSENGER, 'passenger'),
        (OWNER, 'owner'),
    ]
    account_type = models.CharField(max_length=32, choices=ACCOUNT_TYPE, default=PASSENGER)

class Blimp(models.Model):
    id = models.AutoField(primary_key=True, editable=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blimps")
    blimpname = models.TextField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=13)
    description = models.TextField(max_length=1000)
    capacity = models.DecimalField(decimal_places=0, max_digits=4)
    filled_capacity = models.IntegerField(default=0)
    dock = models.TextField(max_length=80, default="None")
    image = models.ImageField(upload_to="blimpUP")
    average_rating = models.DecimalField(decimal_places=1, max_digits=2, default=None, null=True )
    longitude = models.TextField(max_length=40, default=0)
    latitude = models.TextField(max_length=40, default=0)
    WAITING = 'waiting'
    IN_USE = 'in_use'
    STATUSES = [
        (WAITING, 'waiting'),
        (IN_USE, 'in_use'),
    ]
    status = models.CharField(max_length=32, choices=STATUSES, default=WAITING)

class Passenger(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, related_name="is_passenger")
    owner = models.ForeignKey(User, on_delete=CASCADE, related_name="requests")
    blimp = models.ForeignKey(Blimp, on_delete=CASCADE, null=True, related_name="passengers")
    AWAITING = 'awaiting'
    ACCEPTED = 'accepted'
    STATUSES = [
        (AWAITING, 'awaiting'),
        (ACCEPTED, 'accepted'),
    ]
    status = models.CharField(max_length=32, choices=STATUSES, default=AWAITING)

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, related_name="reviews")
    blimp = models.ForeignKey(Blimp, on_delete=CASCADE, related_name="reviews")
    comment = models.TextField(max_length=300)
    datetime = models.DateField(auto_now_add=True)
    rating = models.IntegerField()

class ReviewCharge(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE, related_name="review_charges")
    blimp = models.ForeignKey(Blimp, on_delete=CASCADE, related_name="review_charges")