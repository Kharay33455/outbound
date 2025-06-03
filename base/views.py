from django.shortcuts import render
from .consumers import get_running_values
from django.http import JsonResponse, HttpResponse
import requests
# Create your views here.


def index(request):
    return JsonResponse({"msg":"I am awake"}, status = 200)

def cashien_dispute_chat(request):
    if not request.user.is_superuser:
        return HttpResponse(status = 404)
    env = get_running_values()
    context = {"env" : env}
    return render(request, "base/cashien_dispute.html", context)

def cashien_dispute_list(request, auth_cookie, trade_id):
    env = get_running_values()
    if trade_id == "all":
        response = requests.get(env['bh'] + "/cashien/admin-dispute-list", headers={
            "Authorization" : auth_cookie,
            "Content-Type" : "application/json"
        })
        if response.status_code != 200:
            return HttpResponse(status = 404)
        context = {"trades": response.json()['msg'], "auth_cookie" : auth_cookie}
        return render(request, 'base/cashien_list.html', context)
    else:

        context = {"auth_cookie" : auth_cookie, "trade_id" : trade_id, "bh" : env['bh']}
        return render(request, "base/cashien_dispute_chat.html", context)