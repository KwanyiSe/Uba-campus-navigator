# createuser.py just a helper mudule to create a user without using the admin 

import os
import django

# 1Point to your Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "unimap_project.settings")  

# Setup Django
django.setup()

# 3Now you can import models
from django.contrib.auth.models import User
from campus.models import University, CampusAdminUser, Building  # replace 'campus' with your app name


#  Import your models
from django.contrib.auth.models import User
from campus.models import University, CampusAdminUser  # replace 'campus' with your app name

#  Pick a university (or create one if needed)
uni, created = University.objects.get_or_create(
    short_name="Awe",
    defaults={"name": "University of Big Awesomeness", "country": "Cameroon"}
)


# Create a new user
username = "ubadmin"
password = "tedst123"
email = "unisdmin@example.com"


# List all users
for u in User.objects.all():
    print(u.username, u.is_superuser)

# List all CampusAdminUsers
for ca in CampusAdminUser.objects.all():
    print(ca.user.username, ca.university.name, ca.university.short_name)


# Check if user exists
if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(username=username, password=password, email=email)
    # Assign user to university via CampusAdminUser
    CampusAdminUser.objects.create(user=user, university=uni)
    print(f"Created university admin {username} for {uni.name}")
else:
    print(f" \n User {username} already exists!!!!")










# creating a university test Create Harvard University go to the url/harv youll see it
harvard = University.objects.create(
    name="Harvard University",
    short_name="HARV",
    country="USA",
    min_lat=42.3730,
    max_lat=42.3810,
    min_lng=-71.1200,
    max_lng=-71.1130
)

# --- Create a few test buildings for Harvard ---
Building.objects.create(name="Harvard Yard", latitude=42.3745, longitude=-71.1170, university=harvard)
Building.objects.create(name="Science Center", latitude=42.3760, longitude=-71.1180, university=harvard)

# --- Create a university admin user for Harvard ---
user = User.objects.create_user(username="harvard_admin", password="test123")
CampusAdminUser.objects.create(user=user, university=harvard)