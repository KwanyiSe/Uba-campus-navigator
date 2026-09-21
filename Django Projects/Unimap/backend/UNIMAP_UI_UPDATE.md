# UNIMAP UI V4 — Design Alignment

This build aligns the server-rendered UNIMAP frontend with the original dark mobile design reference.

## Design
- Near-black/navy surfaces and glass-like cards
- UNIMAP blue primary action
- Rounded cards, compact spacing, status pills
- Consistent bottom navigation and account/menu hierarchy
- Responsive desktop/mobile layout

## Updated pages
- Landing
- Login
- Registration
- Profile
- Edit Profile
- News
- Classes
- Class Details / Attendance
- Class Management
- Staff Management
- Free Halls
- Place Details
- Navigation
- Feedback
- About / generic Home

## Product terminology
- Campus Now is now **News**
- Meetings have been removed
- News supports Study Groups and Campus News
- Existing academic, attendance, registration and profile functionality is retained
'


# UNIMAP Academic, Attendance & News Update

This build implements the agreed hierarchy University → School → Department → Option → Level/Student.

- Registration uses Full Name and creates an internal username.
- Profiles support profile pictures and Option.
- School Admin appoints registered users as Class Coordinators or Lecturers.
- CCs coordinate an Option + Level cohort; a CC may coordinate multiple cohorts.
- Lecturers are assigned courses.
- Timetables are reference documents. Actual Class Sessions are the source of truth.
- CCs/lecturers can create, start/end, manage and download attendance for actual sessions.
- Student Mark Attendance only succeeds after automatic location verification is supplied. Until campus building geofences are configured, the API intentionally refuses to record attendance; it does not fake a successful check.
- News has only Study Groups and Campus News. Meetings are removed.
- Students can create Study Groups. Appointed staff can create Study Groups and scoped Campus News.
- Posts support multiple attachments and one target audience scope.
- No building coordinates/geofences have been invented; supply them later.

## Safe installation

Use a fresh folder rather than merging this build into an older project.

1. Extract the ZIP.
2. Copy your existing `backend/.env` into the new build's `backend/.env`. Do not replace source files with the old project.
3. From the new project root run `pipenv shell` (or install the dependencies from the included Pipfile).
4. Enter `backend`.
5. Run `python manage.py migrate`.
6. Run `python manage.py check`.
7. Start with `python manage.py runserver`.

Do **not** run `makemigrations` during installation. The required migrations are already included.


## Testing
No database migration changes are required for this UI-only update.
After replacing/extracting the project, use the existing environment and run:
    python manage.py check
    python manage.py runserver

Do not run makemigrations just for this UI update.
# UNIMAP UI— Design Alignment

This build aligns the server-rendered UNIMAP frontend with the original dark mobile design reference.

## Design
- Near-black/navy surfaces and glass-like cards
- UNIMAP blue primary action
- Rounded cards, compact spacing, status pills
- Consistent bottom navigation and account/menu hierarchy
- Responsive desktop/mobile layout

## Updated pages
- Landing
- Login
- Registration
- Profile
- Edit Profile
- News
- Classes
- Class Details / Attendance
- Class Management
- Staff Management
- Free Halls
- Place Details
- Navigation
- Feedback
- About / generic Home

## Product terminology
- Campus Now is now **News**
- Meetings have been removed
- News supports Study Groups and Campus News
- Existing academic, attendance, registration and profile functionality is retained

## Testing
No database migration changes are required for this UI-only update.
After replacing/extracting the project, use the existing environment and run:
    python manage.py check
    python manage.py runserver

Do not run makemigrations just for this UI update.

# UNIMAP Academic, Attendance & News Update

This build implements the agreed hierarchy University → School → Department → Option → Level/Student.

- Registration uses Full Name and creates an internal username.
- Profiles support profile pictures and Option.
- School Admin appoints registered users as Class Coordinators or Lecturers.
- CCs coordinate an Option + Level cohort; a CC may coordinate multiple cohorts.
- Lecturers are assigned courses.
- Timetables are reference documents. Actual Class Sessions are the source of truth.
- CCs/lecturers can create, start/end, manage and download attendance for actual sessions.
- Student Mark Attendance only succeeds after automatic location verification is supplied. Until campus building geofences are configured, the API intentionally refuses to record attendance; it does not fake a successful check.
- News has only Study Groups and Campus News. Meetings are removed.
- Students can create Study Groups. Appointed staff can create Study Groups and scoped Campus News.
- Posts support multiple attachments and one target audience scope.
- No building coordinates/geofences have been invented; supply them later.

## Safe installation

Use a fresh folder rather than merging this build into an older project.

1. Extract the ZIP.
2. Copy your existing `backend/.env` into the new build's `backend/.env`. Do not replace source files with the old project.
3. From the new project root run `pipenv shell` (or install the dependencies from the included Pipfile).
4. Enter `backend`.
5. Run `python manage.py migrate`.
6. Run `python manage.py check`.
7. Start with `python manage.py runserver`.

Do **not** run `makemigrations` during installation. The required migrations are already included.
