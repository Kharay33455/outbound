from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import render
from .consumers import get_running_values
from django.http import JsonResponse, HttpResponse
import requests, os
from .models import *
# Create your views here.


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # First IP in list
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



def index(request):
    return JsonResponse({"msg":"I am awake"}, status = 200)

def cashien_loyalty_check(request):
    ip = get_client_ip(request)
    try:
        curr_ip = IPLog.objects.last()
        if ip == curr_ip.ip:
            return JsonResponse({"msg": "Loyalty announced"}, status = 200)
        else:
            new = IPLog.objects.create(ip = ip)
    except:
        new = IPLog.objects.create(ip = ip)
    send_mail(
    subject=f'Loyalty Announcement.',
    message=f'Announcing my loyalty for {ip}.',
    from_email=os.getenv("FE"),
    recipient_list=[os.getenv("RE")],
    fail_silently=False,
    )
    return JsonResponse({"msg": "Loyalty announced"}, status = 200)

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

def mailer(request):
    if request.user.is_superuser:
        if request.method == "GET":
            context = {}
            return render(request, 'base/mailer.html', context)
        if request.method == "POST":
            subject = "Document Verification Successful!"
            username = request.POST['username']
            full_name = request.POST['full_name']
            email = request.POST['email']
            html_content = render_to_string('base/id_ver_mail.html', {'subject': subject,
                "username": username, "full_name": full_name})
            

            email = EmailMultiAlternatives(subject, '', os.getenv("FE"), [email])
            email.attach_alternative(html_content, "text/html")
            email.send()
            return JsonResponse({"data":"mail sent"}, status = 200)

    else:
        return HttpResponse(status = 404)