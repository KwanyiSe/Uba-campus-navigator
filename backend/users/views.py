from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from campus.models import University
from accounts.models import Profile
from accounts.serializers import RegisterSerializer, ProfileUpdateSerializer

def ensure_profile(user):
    p=getattr(user,"profile",None)
    if p:return p
    u=University.objects.filter(active=True).first()
    return Profile.objects.create(user=user,university=u,role="student") if u else None

def login_view(request):
    # Authenticated users should never see the login page.
    if request.user.is_authenticated:
        return redirect("campus-map")

    if request.method=="POST":
        identity=request.POST.get("username","").strip(); password=request.POST.get("password","")
        user=authenticate(request,username=identity,password=password)
        if user is None:
            from django.contrib.auth.models import User
            u=User.objects.filter(email__iexact=identity).first()
            if u:user=authenticate(request,username=u.username,password=password)
        if user:
            auth_login(request,user); request.session["show_unimap_splash"]=True; return redirect("campus-map")
        messages.error(request,"Invalid email/username or password.")
    return render(request,"accounts/login.html")

def register_view(request):
    # Authenticated users should never see the registration page.
    if request.user.is_authenticated:
        return redirect("campus-map")

    universities = University.objects.filter(active=True).order_by("name")
    if request.method == "POST":
        data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "password": request.POST.get("password", ""),
            "university": request.POST.get("university") or None,
            "school": request.POST.get("school") or None,
            "department": request.POST.get("department") or None,
            "option": request.POST.get("option") or None,
            "level": request.POST.get("level") or None,
            "matric_number": request.POST.get("matric_number", "").strip() or None,
        }

        if request.FILES.get("profile_picture"):
            data["profile_picture"] = request.FILES["profile_picture"]

        serializer = RegisterSerializer(data=data)

        if serializer.is_valid():
            user = serializer.save()

            auth_login(request, user)
            request.session["show_unimap_splash"] = True

            return redirect("campus-map")

        for field, errors in serializer.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    return render(
        request,
        "accounts/register.html",
        {
            "universities": universities,
            "form_data": request.POST,
        },
    )
    
def logout_view(request):auth_logout(request);return redirect("login")

@login_required(login_url="login")
def profile_view(request):return render(request,"accounts/profile.html",{"profile":ensure_profile(request.user)})

@login_required(login_url="login")
def profile_edit_view(request):
    p=ensure_profile(request.user)
    if request.method=="POST":
        data={k:request.POST.get(k, "") for k in ["full_name","school","department","option","level","matric_number"]}
        for key in ("school", "department", "option", "level", "matric_number"):
            if data.get(key) == "": data[key] = None
        if request.FILES.get("profile_picture"):data["profile_picture"]=request.FILES["profile_picture"]
        s=ProfileUpdateSerializer(p,data=data,partial=True)
        if s.is_valid():s.save();messages.success(request,"Profile updated successfully.");return redirect("profile")
        for field,errors in s.errors.items():
            for e in errors:messages.error(request,f"{field}: {e}")
    return render(request,"accounts/profile_edit.html",{"profile":p,"universities":University.objects.filter(active=True)})

def feedback_page(request):return render(request,"feedback/create.html")
@login_required(login_url="login")
def classes_view(request):return render(request,"classes.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def halls_view(request):return render(request,"halls.html")
@login_required(login_url="login")
def campus_now_view(request):return render(request,"campus_now.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def navigation_view(request):return render(request,"navigation.html")
@login_required(login_url="login")
def place_details_view(request):return render(request,"place_details.html")
@login_required(login_url="login")
def class_detail_view(request):return render(request,"class_detail.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def class_management_view(request):return render(request,"class_management.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def staff_management_view(request):return render(request,"staff_management.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def menu_view(request):return render(request,"menu.html",{"profile":ensure_profile(request.user)})
@login_required(login_url="login")
def notifications_view(request):
    return render(request, "notifications.html")

def about_view(request):return render(request,"about.html")
def landing_view(request):return render(request,"landing.html")
