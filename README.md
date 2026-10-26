# Pocket Consultancy
### Role-Based Education Consultancy Management and Student Guidance System

Pocket Consultancy is a Django-based academic prototype designed to organize education consultancy activities and provide students with structured guidance when exploring international study opportunities.

The system provides role-based dashboards, university and course browsing, rule-based course matching, appointment scheduling, document review, student application tracking, notifications, and counselor notes.

> **Project type:** Academic prototype for BIM 6th-semester project demonstration and external defense. It is not an official university admissions system or a live visa-processing platform.

## Table of Contents

- [Project Objectives](#project-objectives)
- [Key Features](#key-features)
- [User Roles](#user-roles)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation and Setup](#installation-and-setup)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Security and Limitations](#security-and-limitations)
- [Future Enhancements](#future-enhancements)
- [Academic Purpose](#academic-purpose)

## Project Objectives

The primary objectives of Pocket Consultancy are to:

1. Centralize student profiles and education consultancy records.
2. Help students explore countries, universities, and courses.
3. Provide transparent, rule-based course matching using available student information.
4. Organize counseling appointments and counselor availability.
5. Manage student document submissions and reviews.
6. Track application statuses and maintain a history of status changes.
7. Provide role-based access control for different consultancy users.
8. Demonstrate practical application of Python, Django, relational databases, and web development.

## Key Features

### Student Management
- User registration, login, and logout.
- Student profiles and profile editing.
- Role-based dashboards.
- Student-specific application and appointment views.

### Education Catalog
- Browse countries, universities, and courses.
- View catalog details.
- Search and explore available study options.

### Course Matching
- Rule-based matching using available academic information.
- Consideration of study level, academic score, preferred country, and budget where applicable.
- Matching outcomes such as `matches`, `needs_review`, and `insufficient_data`.
- Transparent limitations when required student information is missing.

Course matching is advisory only. It does not guarantee admission or represent official university eligibility decisions.

### Course Shortlisting
- Add courses to a personal shortlist.
- View shortlisted courses.
- Remove courses from the shortlist.
- Prevent duplicate student-course shortlist entries.

### Counseling Appointments
- Book appointments.
- Manage counselor availability.
- View appointment records.
- Support appointment cancellation and availability-slot restoration.
- Manage appointment statuses according to user permissions.

### Document Management
- Upload supported PDF, JPG, JPEG, and PNG files.
- Enforce a configured maximum upload size of 5 MB.
- Review submitted documents.
- Record approval or rejection decisions and review feedback.
- Restrict document access through application permissions.

File extension and size validation do not establish that a document is authentic or safe. Production use requires stronger file validation and malware scanning.

### Student Application Tracking
- Create student application records.
- Generate application reference numbers.
- Track application statuses.
- Maintain application status history.
- Notify relevant users about application updates.

Application statuses include:

- Submitted
- Under Review
- Documents Required
- Shortlisted
- Offer Received
- Rejected
- Withdrawn

These statuses represent records inside this prototype; they do not indicate decisions made by real universities.

### Notifications and Counselor Notes
- View personal notifications.
- Mark notifications as read.
- Allow authorized counselors to create and manage counseling notes.
- Restrict access to notes according to role and permissions.

## User Roles

| Role | Main Responsibilities |
|---|---|
| Student | Manage profile, explore courses, shortlist options, book appointments, upload documents, track applications, and view notifications. |
| Counselor | Review applications, manage appointments, and maintain counseling notes for assigned or selected student records according to permissions. |
| Documentation Officer | Review submitted documents and record document decisions and feedback. |
| Administrator | Manage system records and oversee users, applications, documents, and operational information. |

Access to pages and actions is controlled by the application's role-based permissions.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Django | Web framework, request handling, authentication, and application logic |
| SQLite | Default development database |
| PostgreSQL | Optional database configuration, if enabled and configured |
| HTML5 | Page structure |
| CSS | Styling and layout |
| JavaScript | Client-side interactions where implemented |
| Django ORM | Database models and queries |
| Django Admin | Administrative data management |
| Git and GitHub | Version control and source-code hosting |

## Project Structure

```text
pocket-consultancy/
├── accounts/
│   ├── migrations/
│   ├── admin.py
│   ├── decorators.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── core/
│   ├── migrations/
│   ├── admin.py
│   ├── forms.py
│   ├── matching.py
│   ├── models.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/
│   ├── accounts/
│   ├── core/
│   └── base.html
├── .env.example
├── .gitignore
├── manage.py
└── requirements.txt
```

The `accounts` app handles user accounts and role-related functionality. The `core` app contains the primary consultancy features, models, and business logic. The `config` directory contains the Django project configuration.

## Installation and Setup

### Prerequisites

Install the following before running the project:

- Python compatible with the project's installed Django version.
- Git.
- A terminal such as Windows PowerShell.
- A code editor such as Visual Studio Code.

### 1. Clone the repository

```powershell
git clone https://github.com/nikesh623/pocket-consultancy.git
cd pocket-consultancy
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, consult the Python documentation or activate the environment through your IDE without changing system-wide security settings unnecessarily.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace placeholder values with appropriate local development settings. Generate a development secret key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Use the generated value for `SECRET_KEY` in `.env`. Configure the environment variables according to `config/settings.py`.

**Never commit `.env` or publish a real secret key.** The repository's `.gitignore` excludes the local environment file.

### 5. Apply database migrations

```powershell
python manage.py migrate
```

This creates or updates the local database schema.

### 6. Create an administrator account

```powershell
python manage.py createsuperuser
```

Follow the prompts to create your local administrative account.

## Running the Application

Start the Django development server:

```powershell
python manage.py runserver
```

Open the local application:

- Application: http://127.0.0.1:8000/
- Django administration: http://127.0.0.1:8000/admin/

The development server is intended for local development and demonstration, not production hosting.

## Testing

The project includes automated Django tests for important application functionality, including access control and core workflows.

Run the system check:

```powershell
python manage.py check
```

Run the automated tests:

```powershell
python manage.py test
```

Check changes for whitespace errors before committing:

```powershell
git diff --check
```

**Latest recorded test result:** 58 tests passed during local development. Run the test suite again after making changes to verify the current version.

## Security and Limitations

Pocket Consultancy is an academic prototype. The following limitations should be considered:

- Sample or demonstration records may be used during evaluation.
- Course matching is rule-based and does not connect to official admissions systems.
- No admission, scholarship, visa, or immigration outcome is guaranteed.
- Document review is an internal workflow, not official document authentication.
- No real payment processing or live university integration is implied.
- Local SQLite data and uploaded media are excluded from version control.
- Production deployment requires a secure secret-management strategy, HTTPS, production database configuration, secure cookie settings, appropriate host validation, static/media storage configuration, backups, and stronger uploaded-file security.

Use synthetic demonstration records rather than real student identity documents when demonstrating the application publicly.

## Future Enhancements

Possible future improvements include:

- Responsive user-interface refinements.
- Advanced filtering and reporting.
- Email notifications.
- More comprehensive audit logging.
- Enhanced file-signature validation and malware scanning.
- Automated backup and recovery procedures.
- PostgreSQL deployment.
- Deployment to a production hosting platform.
- Improved accessibility and usability.
- Integration with verified external education data sources where authorized.

These are potential improvements, not claims that they are already implemented.

## Academic Purpose

This project demonstrates the application of web development and software engineering concepts in an education consultancy scenario, including:

- Role-based access control.
- Database design and relational data management.
- Authentication and authorization.
- CRUD operations.
- Form validation.
- Business-rule implementation.
- Workflow and status management.
- Automated testing.
- Version control using Git and GitHub.

It is intended to support academic learning, practical demonstration, and further development.

## Author

**Nikesh Kumar Sah**

BIM Student | Aspiring IT Professional

GitHub: [@nikesh623](https://github.com/nikesh623)

Project repository: [Pocket Consultancy](https://github.com/nikesh623/pocket-consultancy)

---

*Built with Python and Django as an academic software development project.*
