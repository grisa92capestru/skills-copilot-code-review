# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements in the header banner
- Manage announcements (create, edit, delete) for signed-in teachers

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements`                                                  | Get active announcements (date-filtered by start and expiration)    |
| GET    | `/announcements/manage?username=teacher_user`                     | Get all announcements for management (signed-in users only)         |
| POST   | `/announcements?username=teacher_user`                            | Create an announcement (expiration required, start optional)        |
| PUT    | `/announcements/{announcement_id}?username=teacher_user`          | Update an announcement                                              |
| DELETE | `/announcements/{announcement_id}?username=teacher_user`          | Delete an announcement                                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:
   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB collections and initialized with example content when collections are empty.
