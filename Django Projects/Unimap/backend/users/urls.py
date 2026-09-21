from django.urls import path
from . import views


urlpatterns=[
 path("",views.landing_view,name="landing"),path("login/",views.login_view,name="login"),path("register/",views.register_view,name="register_page"),
 path("profile/",views.profile_view,name="profile"),path("profile/edit/",views.profile_edit_view,name="profile_edit"),path("feedback/",views.feedback_page,name="feedback"),
 path("classes/",views.classes_view,name="classes"),path("halls/",views.halls_view,name="halls"),path("campus-now/",views.campus_now_view,name="campus-now"),
 path("navigation/",views.navigation_view,name="navigation"),path("place/",views.place_details_view,name="place-details"),path("class/",views.class_detail_view,name="class-detail"),
 path("class-management/",views.class_management_view,name="class-management"),path("staff-management/",views.staff_management_view,name="staff-management"),
 path("menu/",views.menu_view,name="menu"),path("about/",views.about_view,name="about"),path("logout/",views.logout_view,name="logout")]
