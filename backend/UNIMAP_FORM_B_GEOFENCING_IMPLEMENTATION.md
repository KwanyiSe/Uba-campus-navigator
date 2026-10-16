# UNIMAP Form B + Geofencing implementation
..
## Form B flow
1. Admin/School Admin creates an Academic Year and its two Semesters.
2. CC selects Academic Year, Semester, Department, Option and Level.
3. CC uploads Form B.
4. The server parses PDF/Excel/Word/CSV/TXT and extracts course code + course title.
5. Existing Course records are reused by university + course code; missing courses are created.
6. FormBCourse stores the exact courses found in that semester's Form B.
7. Publishing matches students by university/school/department/option/level and creates semester/Form-B-scoped enrollments.
8. Class sessions can reference the Form B and attendance checks the student's enrollment.

## Geofencing
- Building.geofence stores a polygon as `[[lat, lng], ...]`.
- Admin can manage the polygon in the Django admin.
- Attendance requires an active class, current date, matching cohort, active enrollment, assigned building, valid polygon, and a GPS point inside the polygon.
- The server does not trust a client `location_verified` boolean.
- Attendance records store latitude, longitude, accuracy and verification time for auditability.


## Automatic class ending
A class can only be started on its scheduled date after `start_time` and before `end_time`. The CC may still end a class early with the End Class action. Once `end_time` is reached, the server considers the session closed, reconciles it to `completed` when the academic APIs are touched, and attendance has an explicit end-time guard, so a forgotten End Class button cannot keep attendance open.
Base is now set!