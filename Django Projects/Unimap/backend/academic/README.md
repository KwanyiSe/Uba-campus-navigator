# UNIMAP academic backend

This app is the backend foundation for the Classes, Campus Now, attendance and map activity UI. It is installed in `unimap_project.settings` and exposed under `/api/academic/`.

## Endpoints

- `/api/academic/courses/?university=UBa`
- `/api/academic/sessions/?university=UBa`
- `/api/academic/classes/` — authenticated user's enrollments
- `/api/academic/schedule/` — authenticated user's scheduled sessions
- `/api/academic/attendance/` — authenticated user's attendance records
- `/api/academic/halls/?university=UBa` — hall availability derived from current class sessions
- `/api/academic/activities/?university=UBa` — current classes + campus activities
- `/api/academic/overview/?university=UBa` — campus academic overview

## Admin data model

Create and manage `Course`, `ClassSession`, `Enrollment`, `AttendanceRecord`, and `CampusActivity` from the custom Campus Admin.

Buildings also now have `floor`, `capacity`, `status`, and `opening_hours` fields for the map Place Details UI.

## Local demo data

After creating at least one active university and one building in the custom admin:

```bash
python manage.py migrate
python manage.py seed_academic_demo --university UBa
```

The seed command is optional and only creates test academic/activity records. It does not delete existing records.
