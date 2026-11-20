from django.http import HttpResponse


def index(request):
    return HttpResponse("Inventory Management API is running!")
