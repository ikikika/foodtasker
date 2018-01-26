import json

from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from oauth2_provider.models import AccessToken

from foodtaskerapp.models import Restaurant, Meal, Order, OrderDetails
from foodtaskerapp.serializers import RestaurantSerializer, MealSerializer, OrderSerializer

#customers

def customer_get_restaurants(request):
    restaurants = RestaurantSerializer(
        Restaurant.objects.all().order_by("-id"),
        many = True,
        context = {"request": request}
    ).data

    return JsonResponse({"restaurants": restaurants})

def customer_get_meals(request, restaurant_id):
    meals = MealSerializer(
        Meal.objects.filter(restaurant_id = restaurant_id).order_by("-id"),
        many = True,
        context = {"request": request}
    ).data
    return JsonResponse({"meals": meals})

@csrf_exempt
def customer_add_order(request):
    """
        access_token
        restaurant_id
        address
        order_details = [{"meal_id":4, "quantity": 1}, {"meal_id":2, "quantity": 2}]
        stripe_token
    """
    if request.method == "POST":
        #get token
        access_token = AccessToken.objects.get(token = request.POST.get("access_token"),
            expires__gt = timezone.now())
        #get profile from token
        customer = access_token.user.customer
        #check whether customer has any order that is not delivered
        if Order.objects.filter(customer = customer).exclude(status = Order.DELIVERED):
            return JsonResponse({"status":"fail", "error":"Your last order must be completed"})
        #check if address provided
        if not request.POST["address"]:
            return JsonResponse({"status": "fail", "error": "Address is required"})
        #get order details
        order_details = json.loads(request.POST["order_details"])

        order_total = 0
        for meal in order_details:
            order_total += Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]

        if len(order_details) > 0:
            #step 1 - create order
            order = Order.objects.create(
                customer = customer,
                restaurant_id = request.POST["restaurant_id"],
                total = order_total,
                status = Order.COOKING,
                address = request.POST["address"]
            )
            #step 3 - create order details
            for meal in order_details:
                OrderDetails.objects.create(
                    order = order,
                    meal_id = meal["meal_id"],
                    quantity = meal["quantity"],
                    subtotal = Meal.objects.get(id = meal["meal_id"]).price * meal["quantity"]
                )
            return JsonResponse({"status": "success"})


def customer_get_latest_order(request):
    access_token = AccessToken.objects.get(token = request.GET.get("access_token"),
        expires__gt = timezone.now())
    customer = access_token.user.customer
    order = OrderSerializer(Order.objects.filter(customer = customer).last()).data
    return JsonResponse({"order": order})

#restaurant

def restaurant_order_notification(request, last_request_time):
    notification = Order.objects.filter(restaurant = request.user.restaurant,
        created_at__gt = last_request_time).count()
    #select count(*) from Orders where reatuarant-request.user.restaurant adn created_at > last_request_time
    return JsonResponse({"notification": notification})


#driver

def driver_get_ready_orders(request):
    return JsonResponse({})

def driver_pick_order(request):
    return JsonResponse({})

def driver_get_latest_order(request):
    return JsonResponse({})

def driver_complete_order(request):
    return JsonResponse({})

def driver_get_revenue(request):
    return JsonResponse({})
