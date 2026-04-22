# Architecture Audit Report — task-manager

**Date:** 2026-04-21
**Auditor:** Kiro (refactor-arch)

---

## Project Summary

| Field | Value |
|-------|-------|
| Language | Python 3.x |
| Framework | Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 |
| Dependencies | flask-cors, marshmallow (unused), requests, python-dotenv (unused) |
| Domain | REST API for task management with users, categories, and reports |
| Architecture | Partial layers (models/, routes/, services/, utils/) |
| Source files | 12 files analyzed |
| DB/Storage | SQLite (tasks.db) — tables: tasks, users, categories |

---

## Findings

### CRITICAL

#### F-01 — Password hashing with MD5
- **File:** `models/user.py:18-22`
- **Problem:** `set_password` and `check_password` use `hashlib.md5` for password hashing. MD5 is cryptographically broken, unsalted, and vulnerable to rainbow tables and brute-force.
- **Impact:** Total password compromise if database is leaked.
- **Recommendation:** Replace with `werkzeug.security.generate_password_hash` / `check_password_hash` (already available via Flask) or `bcrypt`.

#### F-02 — Hardcoded SECRET_KEY
- **File:** `app.py:13`
- **Problem:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` — secret key in plain text in source code.
- **Impact:** Anyone with repo access can forge sessions/tokens.
- **Recommendation:** Read from environment variable via `os.environ` or `python-dotenv` (already in dependencies but unused).

#### F-03 — Hardcoded SMTP credentials
- **File:** `services/notification_service.py:8-9`
- **Problem:** `email_user = 'taskmanager@gmail.com'` and `email_password = 'senha123'` in plain text.
- **Impact:** Email credentials exposed in repository.
- **Recommendation:** Move to environment variables.

#### F-04 — Password exposed in User response
- **File:** `models/user.py:12-13`
- **Problem:** `to_dict()` includes `'password': self.password` — password hash returned in all responses that serialize the user.
- **Impact:** Password hash leakage to any API client.
- **Recommendation:** Remove `password` field from `to_dict()`.

#### F-05 — Fake authentication token
- **File:** `routes/user_routes.py:120-121`
- **Problem:** `'token': 'fake-jwt-token-' + str(user.id)` — predictable token, unsigned, no expiration.
- **Impact:** Anyone can forge tokens for any user.
- **Recommendation:** Implement real JWT with `PyJWT` or `flask-jwt-extended`, or at minimum use `itsdangerous` (included in Flask).

#### F-06 — SQL Injection via LIKE
- **File:** `routes/task_routes.py:131-135`
- **Problem:** `Task.title.like(f'%{query}%')` — request parameter interpolated directly into LIKE pattern without sanitizing special characters `%` and `_`.
- **Impact:** Search query manipulation; potential injection with less secure drivers.
- **Recommendation:** Use `Task.title.contains(query)` or escape LIKE special characters.

#### F-07 — No endpoint protected by authentication
- **File:** All files in `routes/`
- **Problem:** No route checks token or session. Anyone can create/delete users, tasks, and categories.
- **Impact:** Unrestricted access to all API operations, including administrative ones.
- **Recommendation:** Add authentication middleware and role-based authorization decorators.

### HIGH

#### F-08 — Debug mode in production
- **File:** `app.py:31`
- **Problem:** `app.run(debug=True)` — debug mode active, exposes Werkzeug interactive debugger.
- **Impact:** Remote arbitrary code execution via debugger PIN.
- **Recommendation:** Read `debug` from environment variable, default `False`.

#### F-09 — Hardcoded Database URI
- **File:** `app.py:11`
- **Problem:** `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'` — hardcoded, no way to configure per environment.
- **Impact:** Cannot use different database in staging/production without code changes.
- **Recommendation:** Read from environment variable with SQLite fallback for dev.

#### F-10 — Duplicated business logic (overdue) in 7 locations
- **Files:** `models/task.py:42-51`, `routes/task_routes.py:22-31`, `routes/task_routes.py:56-64`, `routes/task_routes.py:175-183`, `routes/report_routes.py:33-42`, `routes/report_routes.py:107-110`, `routes/user_routes.py:100-108`
- **Problem:** The "overdue task" logic is copy-pasted in at least 7 places.
- **Impact:** Any rule change must be replicated in 7 points; high risk of inconsistency.
- **Recommendation:** Centralize in `Task.is_overdue()` (already exists but unused) and call from all points.

#### F-11 — Duplicated manual serialization (to_dict bypass)
- **Files:** `routes/task_routes.py:13-44`, `routes/user_routes.py:85-108`
- **Problem:** `get_tasks()` and `get_user_tasks()` build dicts manually instead of using `Task.to_dict()`.
- **Impact:** Fields added to model may not appear in all endpoints.
- **Recommendation:** Use `Task.to_dict()` consistently and add `overdue` field to it.

#### F-12 — N+1 queries in GET /tasks
- **File:** `routes/task_routes.py:34-46`
- **Problem:** For each task, queries `User.query.get(t.user_id)` and `Category.query.get(t.category_id)` — 2 extra queries per task.
- **Impact:** With 100 tasks, 201 queries instead of 1.
- **Recommendation:** Use `joinedload` or access `t.user.name` with eager loading.

#### F-13 — N+1 queries in GET /categories and /reports/summary
- **Files:** `routes/report_routes.py:131-135`, `routes/report_routes.py:56-68`
- **Problem:** Per-record queries for counts and task lists.
- **Impact:** Queries grow linearly with record count.
- **Recommendation:** Use `db.func.count` with GROUP BY.

#### F-14 — Category routes mixed into report_routes
- **File:** `routes/report_routes.py:125-180`
- **Problem:** Category CRUD is inside `report_routes.py`, violating separation of concerns.
- **Impact:** Hard to maintain and discover endpoints.
- **Recommendation:** Move to `routes/category_routes.py`.

### MEDIUM

#### F-15 — Bare except swallowing errors
- **Files:** Multiple locations across `routes/task_routes.py`, `routes/user_routes.py`, `routes/report_routes.py`
- **Problem:** `except:` without exception type catches everything including `SystemExit`, `KeyboardInterrupt`, with no real error logging.
- **Impact:** Silent bugs; impossible to diagnose failures in production.
- **Recommendation:** Use `except Exception as e:` with structured logging.

#### F-16 — Logging via print()
- **Files:** `routes/task_routes.py`, `routes/user_routes.py`, `services/notification_service.py`, `utils/helpers.py`
- **Problem:** All "observability" is via `print()` — no level, no standardized timestamp, no configurable destination.
- **Impact:** Logs lost in production; impossible to filter by severity.
- **Recommendation:** Use `logging` stdlib with centralized configuration.

#### F-17 — Duplicated validation between routes and helpers
- **Files:** `routes/task_routes.py:80-100` vs `utils/helpers.py:42-80`
- **Problem:** `process_task_data()` in helpers does the same validation as route handlers, but neither uses the other.
- **Impact:** Validation rules silently diverge.
- **Recommendation:** Centralize validation (ideally with marshmallow schemas).

#### F-18 — `type(x) == list` instead of `isinstance`
- **Files:** `routes/task_routes.py:112`, `routes/task_routes.py:157`, `utils/helpers.py:72`
- **Problem:** `type(tags) == list` doesn't work with list subclasses.
- **Recommendation:** Use `isinstance(tags, list)`.

#### F-19 — `datetime.utcnow()` deprecated
- **Files:** All models, routes, services, utils
- **Problem:** `datetime.utcnow()` is deprecated since Python 3.12 — returns naive datetime without timezone.
- **Recommendation:** Use `datetime.now(datetime.timezone.utc)`.

#### F-20 — No pagination on list endpoints
- **Files:** GET /tasks, GET /users, search
- **Problem:** All list endpoints return all records without limit/offset.
- **Recommendation:** Add `page` and `per_page` parameters.

#### F-21 — Unused imports
- **Files:** `app.py:8`, `routes/task_routes.py:7`, `routes/user_routes.py:5`, `utils/helpers.py:4-7`
- **Recommendation:** Remove unused imports.

#### F-22 — Marshmallow in dependencies but unused
- **File:** `requirements.txt:4`
- **Recommendation:** Create marshmallow schemas for validation and serialization.

#### F-23 — python-dotenv in dependencies but unused
- **File:** `requirements.txt:6`
- **Recommendation:** Call `load_dotenv()` in entry point and use `os.environ` for configs.

### LOW

#### F-24 — Manual cascade deletion of tasks when deleting user
- **File:** `routes/user_routes.py:80-82`
- **Recommendation:** Configure `cascade='all, delete-orphan'` on relationship.

#### F-25 — Constants defined but not used consistently
- **File:** `utils/helpers.py:83-90`
- **Recommendation:** Import and use constants from a single source.

#### F-26 — Notifications stored in memory
- **File:** `services/notification_service.py:6`
- **Recommendation:** Persist to database if history is needed.

---

**Total: 26 findings (7 CRITICAL, 7 HIGH, 9 MEDIUM, 3 LOW)**
