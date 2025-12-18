# Face Attendance System

Flask + React based face attendance platform with InsightFace embeddings, session-aware attendance, and a background scheduler for timetable automation.

## Highlights
- **Smart sessions**: manual sessions auto-activate when starting now/within 5 minutes; future sessions stay scheduled and auto-activate via the scheduler. Active session lookups ignore expired windows.
- **Scheduler jobs**: creates sessions from the timetable and now also auto-activates scheduled sessions when their start time arrives.
- **Enrollment-aware recognition**: recognition only marks attendance for students enrolled in the active session’s course and logs re-entry.
- **Safer CRUD**: duplicate student IDs rejected, email validation on updates, manual attendance requires a valid session/enrollment, and timetable/course/session endpoints perform overlap and dependency checks.
- **Performance**: new DB indexes for common queries and a `notes` field on sessions for admin context (see migration script below).

## Quick Start
### Backend
1. `python -m venv venv && venv\\Scripts\\activate` (or use your preferred environment)
2. `pip install -r backend/requirements.txt`
3. Set env vars (create `backend/.env` if needed):
   - `DATABASE_URL=sqlite:///data.db`
   - `UPLOAD_FOLDER=uploads`
4. Initialize/upgrade the database:
   - `python backend/app.py` (first run creates tables), then
   - `python backend/migrations/add_indexes.py` to add indexes and the `sessions.notes` column.
5. Start the API: `python backend/app.py` (runs on `http://localhost:5000`).

### Frontend
1. `cd frontend`
2. `npm install`
3. `echo "VITE_API_URL=http://localhost:5000" > .env`
4. `npm run dev` (default `http://localhost:5173`)

## API Notes
- Session management lives under `/api/sessions`; use `POST /api/sessions/manual/create` for manual sessions and `GET /api/sessions/status` for an overview (active, next scheduled, counts, last completed).
- Recognition endpoint `/api/recognize` now blocks students who are not enrolled in the active session’s course.
- Manual attendance endpoint `/api/attendance/mark` requires both `studentId` and `sessionId` and validates enrollment.

## Testing & Maintenance
- Legacy/unit tests are organized under `tests/` (`tests/backend` and `tests/legacy`).
- Scheduler starts automatically with the Flask app; it checks timetable slots every minute and auto-activates scheduled sessions.
- Additional operational guidance: `DEPLOYMENT_GUIDE.md` and `DATABASE_MANAGEMENT_GUIDE.md`.

## Repository Layout
- `backend/` – Flask API, scheduler service, migrations, and ORM models.
- `frontend/` – React client.
- `ml_cvs/` – ML/face recognition helpers.
- `tests/` – existing regression/legacy tests relocated out of the app roots.
