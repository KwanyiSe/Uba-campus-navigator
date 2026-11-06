"""
UNIMAP - Team Permissions Setup Script

Run with:
    python manage.py shell < setup_groups.py

Or interactively:
    python manage.py shell
    >>> exec(open('setup_groups.py').read())

This script is idempotent - safe to run multiple times.
It will create or update the following groups:
    - Backend Developers
    - Frontend Developers
    - Class Coordinators
    - Lecturers
    - School Admins
"""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

print("=" * 60)
print("UNIMAP - Setting up team groups and permissions")
print("=" * 60)


# ============================================================
# Helper: get permission object by app_label.model.codename
# ============================================================
def get_perm(app_label, model, codename):
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        return Permission.objects.get(content_type=ct, codename=codename)
    except (ContentType.DoesNotExist, Permission.DoesNotExist):
        return None


# ============================================================
# Helper: build a list of permissions from a spec
# spec format: [(app_label, model, [codename, codename, ...]), ...]
# ============================================================
def build_permissions(spec):
    perms = []
    missing = []
    for app_label, model, codenames in spec:
        for codename in codenames:
            p = get_perm(app_label, model, codename)
            if p:
                perms.append(p)
            else:
                missing.append(f"{app_label}.{model}.{codename}")
    if missing:
        print(f"  ⚠️  Missing permissions (skipped):")
        for m in missing:
            print(f"      - {m}")
    return perms


# ============================================================
# Helper: create or update a group
# ============================================================
def setup_group(name, spec):
    print(f"\n📦 Group: {name}")
    group, created = Group.objects.get_or_create(name=name)
    if created:
        print(f"   ✅ Created new group")
    else:
        print(f"   🔄 Group already exists - updating permissions")

    perms = build_permissions(spec)
    group.permissions.set(perms)
    group.save()

    print(f"   ✅ Assigned {len(perms)} permissions")
    return group


# ============================================================
# 1. BACKEND DEVELOPERS
# ============================================================
backend_dev_spec = [
    ("campus", "university",       ["view", "change"]),
    ("campus", "building",         ["view", "add", "change"]),
    ("campus", "buildinggeofence", ["view", "add", "change"]),
    ("campus", "geofencelog",      ["view"]),
    ("campus", "sitevisit",        ["view"]),
    ("campus", "dailystats",       ["view"]),
    ("accounts", "school",         ["view", "add", "change"]),
    ("accounts", "department",     ["view", "add", "change"]),
    ("accounts", "option",         ["view", "add", "change"]),
    ("accounts", "profile",        ["view", "change"]),
    ("academic", "course",         ["view"]),
    ("academic", "timetable",      ["view"]),
    ("academic", "formb",          ["view"]),
    ("academic", "classsession",   ["view"]),
    ("academic", "attendancerecord", ["view"]),
    ("feedback", "feedback",       ["view"]),
]

# ============================================================
# 2. FRONTEND DEVELOPERS
# ============================================================
frontend_dev_spec = [
    ("campus", "university",       ["view"]),
    ("campus", "building",         ["view"]),
    ("campus", "sitevisit",        ["view"]),
    ("accounts", "school",         ["view"]),
    ("accounts", "department",     ["view"]),
    ("accounts", "option",         ["view"]),
    ("accounts", "profile",        ["view"]),
    ("academic", "course",         ["view"]),
    ("academic", "timetable",      ["view"]),
    ("academic", "classsession",   ["view"]),
    ("academic", "newspost",       ["view"]),
    ("feedback", "feedback",       ["view"]),
]

# ============================================================
# 3. CLASS COORDINATORS
# ============================================================
cc_spec = [
    ("academic", "course",         ["view"]),
    ("academic", "classsession",   ["add", "change", "view"]),
    ("academic", "classcoordinatorassignment", ["view"]),
    ("academic", "attendancerecord", ["view"]),
    ("academic", "formb",          ["add", "view"]),
    ("academic", "formbcourse",    ["add", "view"]),
    ("academic", "timetable",      ["add", "view"]),
    ("academic", "campusactivity", ["add", "change", "view"]),
    ("accounts", "profile",        ["view"]),
    ("campus", "building",         ["view"]),
]

# ============================================================
# 4. LECTURERS
# ============================================================
lecturer_spec = [
    ("academic", "course",         ["view"]),
    ("academic", "classsession",   ["view"]),
    ("academic", "attendancerecord", ["view"]),
    ("academic", "enrollment",     ["view"]),
    ("accounts", "profile",        ["view"]),
    ("campus", "building",         ["view"]),
]

# ============================================================
# 5. SCHOOL ADMINS
# ============================================================
school_admin_spec = [
    ("accounts", "school",         ["add", "change", "view"]),
    ("accounts", "department",     ["add", "change", "view"]),
    ("accounts", "option",         ["add", "change", "view"]),
    ("accounts", "profile",        ["view", "change"]),
    ("academic", "classcoordinatorassignment", ["add", "change", "view"]),
    ("academic", "course",         ["view"]),
    ("campus", "building",         ["view"]),
    ("campus", "university",       ["view"]),
]


# ============================================================
# RUN SETUP
# ============================================================
print("\n" + "=" * 60)
print("Creating groups...")
print("=" * 60)

setup_group("Backend Developers",  backend_dev_spec)
setup_group("Frontend Developers", frontend_dev_spec)
setup_group("Class Coordinators",  cc_spec)
setup_group("Lecturers",           lecturer_spec)
setup_group("School Admins",       school_admin_spec)

print("\n" + "=" * 60)
print("✅ ALL GROUPS SET UP SUCCESSFULLY")
print("=" * 60)

# Summary
print("\n📋 Summary of groups and their permission counts:")
for g in Group.objects.all().order_by("name"):
    print(f"   • {g.name}: {g.permissions.count()} permissions")

print("\n💡 Next steps:")
print("   1. Go to /admin/auth/user/")
print("   2. Click a user")
print("   3. Check 'Staff status' ✅")
print("   4. Leave 'Superuser status' ❌ unchecked")
print("   5. Add them to the appropriate Group")
print("   6. Save")
print()