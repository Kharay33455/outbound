from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
# Create your views here.

@csrf_exempt
def index(request):
    return JsonResponse({"msg":"I am awake"}, status = 200)
