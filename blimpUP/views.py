from statistics import mean
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models.query import RawQuerySet
from django.db.utils import Error
from django.forms.utils import ErrorDict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django import forms
import os
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import *
from blimpUP.models import *
from json import dumps, loads
from PIL import Image

# Login view
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        if not username or not password:
            return render(request, "blimpUP/login.html", {
                "message": "All fields must be filled.",
                "username": username,
                "password": password
            })

        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "blimpUP/login.html", {
                "message": "Invalid username and/or password.",
                "username": username,
                "password": password
            })
    else:
        return render(request, "blimpUP/login.html")

# Logout view
@login_required(login_url='/login')
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

# Relogin view
@login_required(login_url='/login')
def relogin_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))

# Register view
def register(request):
    message = ""
    account_type = ""

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid(): #Check POST data
            password = form.cleaned_data["password"]
            confirmation = form.cleaned_data["confirmation"]
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            account_type = request.POST.get("account_type", False)
            
            # Ensure password matches confirmation
            if password != confirmation:
                message = "Passwords must match."
            
            # Ensure account type is either owner/passenger
            if account_type not in ["owner", "passenger"]:
                message =  "Wrong account type."
        else: # Send back the form if someting went wrong
            account_type = request.POST.get("account_type", False)
            return render(request, "blimpUP/register.html", {
                    "form": form,
                    "message": message,
                    "selected": account_type
                })

        if message: # Check nothing went wrong
            return render(request, "blimpUP/register.html", {
                    "message": message,
                    "form": form,
                    "selected": account_type
                })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.account_type = account_type
            user.save()
        except IntegrityError: 
            return render(request, "blimpUP/register.html", {
                "message": "Username already taken.",
                "form": form,
                "selected": account_type
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "blimpUP/register.html", {"selected": False})

# Home view
def index(request):

    # Create a list of tuplets, where a tuplete has a blimp object and a False/passenger object
    blimps = []
    is_passenger = False
    pagin_blimps = paginate(request, reverse_list(Blimp.objects.all()), 6)
    for blimp in pagin_blimps:
        for passenger in blimp.passengers.all():
            if passenger.user == request.user:
                is_passenger = True
                blimps.append((blimp, blimp.passengers.filter(user=request.user)[0]))
        if not is_passenger:
            blimps.append((blimp, False))
        is_passenger = False

    

    # Render page
    return render(request, "blimpUP/index.html", {
        "blimps": blimps,
        "pagin_blimps": pagin_blimps,
        "data": dumps({
            "index": True,
            "map": True,
            "blimp_locations": get_blimp_locations(Blimp.objects.all()),
        }),
        "title": "All blimps",
    })

# Register blimp view
@login_required(login_url='/login')
def register_blimp(request):
    if request.method == "POST":
        # Receive data and check it
        blimp_form = BlimpForm(request.POST, request.FILES)
        if blimp_form.is_valid(): # Create blimp 
            blimp = blimp_form.instance
            blimp.owner = request.user
            blimp.save()
            return HttpResponseRedirect(reverse('index'))
        return render(request, "blimpUP/register_blimp.html", {
            'form': blimp_form,
            'data': dumps({
                "map": True,
                "register_blimp_page": True,
                })
        }) # Return form if something went wrong
    else:
        return render(request, "blimpUP/register_blimp.html", {
            "data": dumps({
                "map": True,
                "register_blimp_page": True
            })
        })

# Blimp page
@login_required(login_url='/login')
def blimp_view(request, id):
    message = ""
    if request.method == "GET":
        try: # Check if blimp id exists
            blimp = Blimp.objects.get(id=id)
        except ObjectDoesNotExist: # Return error if blimp id doesn't exist
            return render(request, "blimpUP/blimp.html", {
                "message": format_error("Wrong blimp id.", "")
            })
    elif request.method == "POST": # The post method is for the owner to start/end a blimp trip
        blimp, message = validate_blimp(id) 
        if not message: # If blimp validation went well
            if blimp.owner != request.user: # Check if the blimp owner is the request user
                message = "Error: You do not have permissions for this action"
            else:
                if blimp.status == "in_use": # If blimp was in_use, remove passengers and set status to waiting
                    blimp.status = "waiting"
                    blimp.filled_capacity = 0

                    # Give review charges to passengers of the blimp
                    for passenger in blimp.passengers.all():
                        try: # Pass if user has a review charge
                            passenger_charge = ReviewCharge.objects.get(user=passenger.user, blimp=blimp)
                        except ObjectDoesNotExist: # Create a review charge object if one doesn't exist already
                            passenger_charge = ReviewCharge(user=passenger.user, blimp=blimp)
                            passenger_charge.save()

                    blimp.passengers.all().delete() # Remove all passengers after a trip
                    message = "Ended trip"
                else:
                    blimp.status = "in_use"
                    message = "Started trip"
                blimp.save()
        else:
            message = "Error: Invalid blimp id"
        return HttpResponse(message) # The post request is done with javascript, so a HttpResponse suffices 
        
    passengers = [] # Get all passengers on this blimp
    for passenger in blimp.passengers.all():
        passengers.append(passenger.user)
    
    accepted = True # Check if the user is accepted on the current blimp
    try:
        if Passenger.objects.get(user=request.user, blimp=blimp).status != "accepted":
            accepted = False
    except:
        accepted = False

    can_review = True
    try:
        charges = ReviewCharge.objects.get(user=request.user, blimp=blimp)
    except ObjectDoesNotExist:
        can_review = False

    # Get all paginated reviews
    filter = request.GET.get("filter")
    found = False # Filter all reviews, if a filter is empty or doesn't exist, return default (all reviews or no, if no exist)
    if filter != None:
        if filter in ["oldest", "newest"]:
            if filter == "oldest":
                found = True
                reviews = Review.objects.filter(blimp=blimp)
        elif filter in ["0", "1", "2", "3", "4", "5"]:
            found = True
            reviews = reverse_list(Review.objects.filter(blimp=blimp, rating=int(filter)))
    
    if not found:
        reviews = reverse_list(Review.objects.filter(blimp=blimp))

    pagin_reviews = paginate(request, reviews, 10)

    # Render tempalate
    return render(request, "blimpUP/blimp.html", {
        "blimp": blimp,
        "passengers": passengers,
        "data": dumps({ # For javascript
            "id": blimp.id,
            "capacity": int(blimp.capacity),
            "accepted": accepted,
            "filled_capacity": int(blimp.filled_capacity),
            "map": True,
            "blimp_page": True ,
            "longitude": blimp.longitude,
            "latitude": blimp.latitude
        }),
        "message": message,
        "reviews": pagin_reviews,
        "accepted": accepted,
        "rating_list": [1, 2, 3, 4, 5],
        "can_review": can_review,
        "img_resolution": Image.open(blimp.image.path).size
    })

# Sign up view, used with javascript - returns only a text response
@login_required(login_url='/login')
def sign_up(request):
    message = ""
    if request.method == "POST": 
        # Load data
        body_unicode = request.body.decode('utf-8')
        id = loads(body_unicode)["id"]
        sign_up = loads(body_unicode)["sign_up"]

        blimp, message = validate_blimp(id)

        exists = True # Check if the user is already a passenger on this blimp
        if not message:
            try:
                passenger = Passenger.objects.get(user=request.user, blimp=blimp, owner=blimp.owner)
            except ObjectDoesNotExist:
                exists = False

        if not message:
            if request.user != blimp.owner: # Check that the owner isn't signing up for their own trip
                if sign_up and not exists and blimp.status != "in_use": # Sign up only if the user ins't already a passenger and the blimp isn't in use
                    if blimp.filled_capacity != blimp.capacity: # Check that the blimp capacity isn't full
                        passenger = Passenger(user=request.user, blimp=blimp, owner=blimp.owner)
                        passenger.save()
                        message = "Signed up"
                    else:
                        message = "Error: Blimp capacity full"
                elif not sign_up and exists: # If the user is already a passenger, remove them
                    if passenger.status == 'accepted':
                        passenger.blimp.filled_capacity -= 1
                        passenger.blimp.save()
                    passenger.delete()
                    message = "Removed"
                else:
                    message = "Error: Request data to user alignment"
            else:
                message = "Error: Availability"
    else:
        message = "Error: Wrong request method." # This view is only used with the POST method
    return HttpResponse(message)

# All the requests people placed on one of the owners blimps
@login_required(login_url='/login')
def trip_requests(request):
    message = ""

    if request.method == "POST": # The POST method works along with javascript
        
        # Check and load data
        body_unicode = request.body.decode('utf-8')
        try:
            id = int(loads(body_unicode)["id"])
        except ValueError:
            message = "Error: id value error"

        username = loads(body_unicode)["username"]
        choice = loads(body_unicode)["choice"]

        # Validate request
        if type(id) == int and username and choice in ["accept", "decline"] and not message:            
            try:
                passenger = Passenger.objects.filter(user=User.objects.get(username=username), blimp=Blimp.objects.get(id=id), owner=request.user)[:1].get()

                # If accepted, set the status on the passenger as such
                if choice == "accept":
                    passenger.status = "accepted"
                    passenger.blimp.filled_capacity += 1
                    passenger.blimp.save()
                    passenger.save()
                    message = "OK"
                else: # Else delete the passenger
                    passenger.delete()
                    message = "OK"
            except ObjectDoesNotExist:
                message = "Error: passenger object does not exist"
        else:
            message = "Error: request not valid"
        return HttpResponse(message) # Text response for javascript
    else:
        # Get all requests
        requests = Passenger.objects.filter(owner=request.user)
        trips = []
        for user_request in requests:
            if user_request.status == "awaiting":
                trips.append(user_request)
        
        # Render template
        return render(request, "blimpUP/trip_requests.html", {
            "trip_requests": trips,
            "message": message
        })

# My blimps view - identicall to home page, but only blimps, which belong to the user are shown
@login_required(login_url='/login')
def my_blimps(request):

    # Create a list of tuplets, where a tuplete has a blimp object and a False/passenger object
    blimps = []
    is_passenger = False
    pagin_blimps = paginate(request, reverse_list(Blimp.objects.filter(owner=request.user)), 6)
    for blimp in pagin_blimps:
        for passenger in blimp.passengers.all():
            if passenger.user == request.user:
                is_passenger = True
                if blimp.owner == request.user:
                    blimps.append((blimp, blimp.passengers.filter(user=request.user)[0]))
        if not is_passenger:
            if blimp.owner == request.user:
                blimps.append((blimp, False))
        is_passenger = False

    # Render template
    return render(request, "blimpUP/index.html", {
        "blimps": blimps,
        "pagin_blimps": pagin_blimps,
        "data": dumps({
            "index": True,
            "map": True,
            "blimp_locations": get_blimp_locations(Blimp.objects.filter(owner=request.user)),
        }),
        "my_blimps": True,
        "title": "My blimps"
    })

# My trips view
@login_required(login_url='/login')
def my_trips(request):

    # Get all users trips, where the newest trips are shown above the old trips, but not before the accepted trips
    trips = []
    waiting_trips = []
    for trip in request.user.is_passenger.all():
        if trip.status == "accepted":
            trips.append(trip)
        else:
            waiting_trips.append(trip)
    trips = waiting_trips + trips

    # Render Template
    return render(request, "blimpUP/my_trips.html", {
        "trips": reversed(trips),
        "data": dumps({"index": True}),
    })

# Reviews view - used with javascript
@login_required(login_url='/login')
def review(request, id):
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid(): # Validate form data
            rating = request.POST["rating"]
            comment = form.cleaned_data["comment"]

            blimp, message = validate_blimp(id) # Validate blimp
            if not message and blimp.owner != request.user and int(rating) in [0, 1, 2, 3, 4, 5] and len(comment) <= 300:
                try:
                    # Remove the Review Charge object
                    passenger_review = ReviewCharge.objects.get(user=request.user, blimp=blimp)
                    passenger_review.delete()

                    # Create a review and save it
                    review = Review(user=request.user, blimp=blimp, comment=comment, rating=rating)
                    review.save()

                    # Update the average rating of the blimp
                    rating = average_rating(blimp)
                    blimp.average_rating = rating
                    blimp.save()

                except ObjectDoesNotExist:
                    print("Not enough review charges")
        else:
            rating = request.POST["rating"]
            comment = request.POST["comment"]
            print("Review not valid")
    else:
        print("Expected a POST request, got a GET")
    return redirect('blimp', id=id) # Redirect back to the blimp the user was reviewing

# Edit blimp view
@login_required(login_url='/login')
def edit_blimp(request, id):
    blimp, message = validate_blimp(id)

    if blimp != None: 
        if blimp.owner == request.user:
            if request.method == "GET": # Fill the form with preexisting data of the blimp
                form = NoImageForm(instance=blimp) 

                # Return filled in form template 
                return render(request, "blimpUP/register_blimp.html", {
                    "form": form,
                    "blimp": blimp,
                    "data": dumps({
                        "id": blimp.id,
                        "map": True,
                        "blimp_page": True ,
                        "editing": True,
                        "longitude": blimp.longitude,
                        "latitude": blimp.latitude
                    }),
                    })
            else: 
                no_image_form = NoImageForm(request.POST)
                new_image = False
                if no_image_form.is_valid(): # Validate form
                    try: # Check if the image was changed
                        image = request.FILES.get("image")
                        if image != None:
                            new_image = True
                    except:
                        pass
                    
                    # Change all blimp data
                    blimp.blimpname = no_image_form.cleaned_data["blimpname"]
                    blimp.capacity = no_image_form.cleaned_data["capacity"]
                    blimp.description = no_image_form.cleaned_data["description"]
                    blimp.price = no_image_form.cleaned_data["price"]
                    blimp.dock = no_image_form.cleaned_data["dock"]
                    blimp.longitude = no_image_form.cleaned_data["longitude"]
                    blimp.latitude = no_image_form.cleaned_data["latitude"]
                    if new_image: # If the image was changed, remove the old image and save the new image
                        os.remove(blimp.image.path)
                        blimp.image = request.FILES.get("image")
                    blimp.save()
                    return redirect('blimp', id=id) # Redirect to the blimp the user was editing
                else: # If the form wasn't valid, return filled in data with errors
                    return render(request, "blimpUP/register_blimp.html", {
                        'form': no_image_form,
                        'blimp': blimp,
                        "data": dumps({
                            "id": blimp.id,
                            "map": True,
                            "blimp_page": True ,
                            "editing": True,
                            "longitude": blimp.longitude,
                            "latitude": blimp.latitude
                        }),
                    })
    return redirect("index") # If the blimp doesn't exist, return to home page

# Delete blimp
def delete_blimp(request, id):
    if id: # Check for id
        blimp, message = validate_blimp(id) # Validate blimp
        if not message:
            if request.method == "GET" and request.user == blimp.owner: # Make sure the owner is the one deleting the blimp
                blimp.delete()
    return redirect("index")



# _______________________________________________________________________________________________________
# Helper functions:

def average_rating(blimp):
    average = 0
    for review in blimp.reviews.all():
        average += review.rating
    return round(average/len(blimp.reviews.all()), 1)

# Return blimp instnace with empty message or None (If no blimp under such an id was found) with an error
def validate_blimp(id):
    message = ""
    blimp = None
    try:
        blimp = Blimp.objects.get(id=id)
    except ObjectDoesNotExist:
        message = format_error("Wrong blimp id.", "")
    return blimp, message

# Return formatted error
def format_error(text, error_type):
    if not text: # If no text was provided, use a general error message
        text = "Something went wrong when proccesing your request."
    if not error_type: # If no specific type of style was provided, use the danger styling
        error_type = "danger"

    # Format and return message
    return """ 
            <div class="alert alert-""" + error_type + """ alert-dismissible fade show">
                <strong>Error!</strong> """ + text + """
                <button type="button" class="btn btn-close" data-bs-dismiss="alert"></button>
            </div>
        """

# Paginate function, takes the request, all the objects to be paginated, and the amount by which they will be paginated
def get_blimp_locations(blimps):
    loc_dict = {}
    for blimp in blimps:
        id = blimp.id
        loc_dict[id] = {
            "longitude": blimp.longitude,
            "latitude": blimp.latitude,
            "image": blimp.image.url,
            "blimp_id": blimp.id,
            "blimpname": blimp.blimpname
        }
    return loc_dict


def paginate(request, objects, amount):
    paginator = Paginator(objects, amount)

    # Get page number, if it doesn't exist, start with 1
    page_number = request.GET.get('page')
    if page_number == None:
        page_number = 1

    # If the page doesn't exist, return the first page
    try:
        paginated = paginator.page(page_number)
    except:
        paginated = paginator.page(1)

    return paginated


def reverse_list(lst):
    true_lst = []
    for item in lst:
        true_lst.insert(0, item)
    return true_lst

    