from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarDealer, CarMake, CarModel, DealerReview
from .restapis import get_request, get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request, analyze_review_sentiments
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is None:
        messages.warning(request, "Invalid username or password.")
        return redirect("djangoapp:index")
    else:
        login(request, user)
        messages.success(request, "Login successfully.")
        return redirect('djangoapp:index')

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out user '{}'".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html')
    elif request.method == 'POST':
        username = request.POST['username']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            password = request.POST['password']
            first_name = request.POST['firstname']
            last_name = request.POST['lastname']
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            user.is_superuser = False
            user.is_staff = True
            user.save()  
            login(request, user)
            return redirect("djangoapp:index")
        else:
            messages.warning(request, "The user already exists.")
            return redirect("djangoapp:registration")

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/23053c23-8a47-4c4f-942e-fced897fa2fd/dealership-package/get-dealership"
        dealerships = get_dealers_from_cf(url)
        context["dealership_list"] = dealerships
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, id):
    if request.method == "GET":
        context = {}
        dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/23053c23-8a47-4c4f-942e-fced897fa2fd/dealership-package/get-dealership"
        dealer = get_dealer_by_id_from_cf(dealer_url, id=id)
        context["dealer"] = dealer
    
        review_url = "https://us-south.functions.appdomain.cloud/api/v1/web/23053c23-8a47-4c4f-942e-fced897fa2fd/dealership-package/get-review"
        reviews = get_dealer_reviews_from_cf(review_url, id=id)
        print(reviews)
        context["reviews"] = reviews
        
        return render(request, 'djangoapp/dealer_details.html', context)
            
# View to submit a new review
def add_review(request, id):
    context = {}
    dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/23053c23-8a47-4c4f-942e-fced897fa2fd/dealership-package/get-dealership"
    dealer = get_dealer_by_id_from_cf(dealer_url, id=id)
    context["dealer"] = dealer
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        print(cars)
        context["cars"] = cars
        
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            print(request.POST)
            payload = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
            payload["time"] = datetime.utcnow().isoformat()
            payload["name"] = username
            payload["dealership"] = id
            payload["id"] = id
            payload["review"] = request.POST["content"]
            payload["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    payload["purchase"] = True
            payload["purchase_date"] = request.POST["purchasedate"]           
            payload["car_model"] = car.name
            new_payload = {}
            new_payload["review"] = payload
            review_post_url = "https://us-south.functions.appdomain.cloud/api/v1/web/23053c23-8a47-4c4f-942e-fced897fa2fd/dealership-package/post-review"

            post_request(review_post_url, new_payload, id=id)
        return redirect("djangoapp:dealer_details", id=id)

