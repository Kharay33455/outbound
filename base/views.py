from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.shortcuts import render
from .consumers import get_running_values
from django.http import JsonResponse, HttpResponse
import requests, os,json, random
from .models import *
from django.views.decorators.csrf import csrf_exempt
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
    #send_mail(
    #subject=f'Loyalty Announcement.',
    #message=f'Announcing my loyalty for {ip}.',
    #from_email=os.getenv("FE"),
    #recipient_list=[os.getenv("RE")],
    #fail_silently=False,
    #)
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
            mail_type = request.POST['mail_type']
            
            username = request.POST['username']
            full_name = request.POST['full_name']
            email = request.POST['email']

            if mail_type == "ID VERIFIED":
                subject = "Document Verification Successful!"
                html_content = render_to_string('base/id_ver_mail.html', {'subject': subject,
                    "username": username, "full_name": full_name})
            elif mail_type == "FULLY VERIFIED":
                subject = "Verification Complete!"
                html_content = render_to_string('base/fully_ver_mail.html', {'subject': subject,
                    "username": username})
            
            email = EmailMultiAlternatives(subject, '', os.getenv("FE"), [email])
            email.attach_alternative(html_content, "text/html")
            is_sent = email.send()
            if is_sent > 0:
                return JsonResponse({"data":"mail sent"}, status = 200)
            else:
                return JsonResponse({"data":"mail failed to send"}, status = 400)

    else:
        return HttpResponse(status = 404)

@csrf_exempt
def reset_pass(request):
    body = json.loads(request.body)
    userId = body['userId']
    
    env = get_running_values()
    response = requests.post(env['bh'] + "/cashien/reset-password/", headers={"Content-Type":"application/json"}, json={"userId":userId})
    
    if response.status_code == 400:
        return JsonResponse({'msg':"User does not exist."}, status = 400)
    if response.status_code == 200:
        data = json.loads(response.text)
        
        msg = data['msg']
        subject = "Reset your Cashien account password"
        username = data['username']
        host = body['host']
        content_three = "Thanks for visiting Cashien!"
        content_two = "Cashien will never contact you about this email or ask for any login codes or links. Beware of phishing scams."
        content_one = "Do not share this link with anyone. If you didn't make this request, you can safely ignore this email."
        message = "To reset your password, click on this"
        subheader = "Password verification for " +username
        header = "Hello, "+ username
        email = data['email']
        
        html_content = render_to_string("base/password_reset.html", {"username": username,"verification_link":host+ "/#/reset-password/"+msg,"contentOne":content_one, "contentTwo":content_two, "contentThree":content_three,"message":message, "subheader":subheader,"header":header})
        
        mail_email = EmailMultiAlternatives(subject, '', os.getenv("FE"), [email])
        mail_email.attach_alternative(html_content, "text/html")
        is_send = mail_email.send()
        if is_send > 0:
            return JsonResponse({"msg":"Check your inbox at " + email[0:4] +"***@***.*** to reset your password."}, status = 200)    
        else:
            return JsonResponse({"msg":"Failed to send mail. Try again later"}, status = 400)
            
@csrf_exempt
def set_ver_code(request):
    env = get_running_values()

    body = json.loads(request.body)
    trade_id = body['tradeId']
    amount = body['amount']
    response = requests.get(env['bh'] + "/cashien/set-release-code", headers={"Content-Type":"application/json", "authorization": request.headers['Authorization']}, json={"trade_id":trade_id})
    if response.status_code == 200:
        
        code = str(random.randint(100000, 999999))
        subject = "Release order for " + amount + " USDT on your Cashien account."
        email = json.loads(response.text)['mail']
        contentOne = "An order for " +amount + " USDT has been placed on your account. Use the code below to release the USDT only after you have confirmed that payment has been received in your account."
        passcode = code
        contentTwo = "Cashien would never contact you regarding any links. Please beware of phishing schemes and do not click on suspicious messages or emails claiming to be from us."
        contentThree =  "Thank you for choosing Cashien!"

        html_content = render_to_string("base/mail_with_no_link.html", {"passcode" : code, "header": subject, "contentOne": contentOne, "contentTwo":contentTwo, "contentThree":contentThree})
        mail_sender = EmailMultiAlternatives(subject, '', os.getenv('FE'), [email])
        mail_sender.attach_alternative(html_content, "text/html")
        is_sent = mail_sender.send()
        is_sent = 1
        if is_sent > 0:
            
            release_code, created = ReleaseCode.objects.get_or_create(trade_id = trade_id)
            release_code.code = code
            release_code.save()
            return HttpResponse(status = 204)
        else:
            return HttpResponse(status = 400)
    
    else:
        return JsonResponse({"msg":"An unexpected error has occured."}, status = 400)

@csrf_exempt
def release(request):
    body = json.loads(request.body)
    try:
        code_obj = ReleaseCode.objects.get(trade_id = body['tradeId'], code = body['code'])
        return HttpResponse(status = 204)
    except ReleaseCode.DoesNotExist:
        return HttpResponse(status = 400)



@csrf_exempt
def verify_email(request):
    body = json.loads(request.body)
    env = get_running_values()
    response = requests.post(env['bh'] + "/cashien/verify/get-code/", headers={"Content-Type":"application/json", "Authorization" : request.headers['Authorization']})
    data = json.loads(response.text)
    msg = data['msg']
    
    if response.status_code == 400:
        return JsonResponse({'msg':msg}, status = 400)
    if response.status_code == 200:
        subject = "Verify your email address."
        username = data['username']
        host = body['host']
        content_three = "Thanks for joining Cashien!"
        content_two = "Cashien will never contact you about this email or ask for any login codes or links. Beware of phishing scams."
        content_one = "Do not share this link with anyone. If you didn't make this request, you can safely ignore this email."
        message = "Welcome to Cashien. To complete your verification process, click on this"
        subheader = "Email verification for your Cashien account"
        header = "Hello "+ username + ","
        email = data['email']
        html_content = render_to_string("base/password_reset.html", {"username": username,"verification_link":host+ "/#/verification/"+msg,"contentOne":content_one, "contentTwo":content_two, "contentThree":content_three,"message":message, "subheader":subheader,"header":header})
        mail_email = EmailMultiAlternatives(subject, '', os.getenv("FE"), [email])
        mail_email.attach_alternative(html_content, "text/html")
        is_send = mail_email.send()
        is_send = 0
        if is_send > 0:
            return JsonResponse({"msg":"Check your inbox at " + email[0:4] +"***@***.*** to complete your verification."}, status = 200)    
        else:
            return JsonResponse({"msg":"Failed to send mail. Try again later"}, status = 400)


            
@csrf_exempt
def alert_mail(request):
    env = get_running_values()

    body = json.loads(request.body)
    subject = body['subject']
    email = body['email']
    contentOne = body['contentOne']
    contentTwo = body['contentTwo']
    contentThree =  body['contentThree']
    passcode = body['passcode']
    html_content = render_to_string("base/mail_with_no_link.html", {"passcode" : passcode, "header": subject, "contentOne": contentOne, "contentTwo":contentTwo, "contentThree":contentThree})
    mail_sender = EmailMultiAlternatives(subject, '', os.getenv('FE'), [email])
    mail_sender.attach_alternative(html_content, "text/html")
    mail_sender.send()
    return HttpResponse(status = 204)


@csrf_exempt
def cus_mail(request):
    env = get_running_values()
    
    subject = request.POST['subject']
    email = request.POST['email']
    contentOne = request.POST['cont-one']
    contentTwo = request.POST['cont-two']
    contentThree =  request.POST['cont-three']
    passcode = request.POST['passcode']
    html_content = render_to_string("base/mail_with_no_link.html", {"passcode" : passcode, "header": subject, "contentOne": contentOne, "contentTwo":contentTwo, "contentThree":contentThree})
    mail_sender = EmailMultiAlternatives(subject, '', os.getenv('FE'), [email])
    mail_sender.attach_alternative(html_content, "text/html")
    
    mail_sender.send()
    return HttpResponse(status = 204)


