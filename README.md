# project-S.H.I.T
## Project Overview

This project is a web-based school infrastructure reporting system.

The purpose of this prototype is to help students report damaged school facilities clearly and quickly. The system allows users to submit a report, view reports on a dashboard, check report details, and update report status.

This project is part of my Level 2 Digital Technologies planning and development assessment.

## Sprint 2 Update

End-user feedback from Sprint 1 said that the form was clear, but the student submit area and staff review area should be separated.

In Sprint 2, the prototype was updated to:

- Add a student page for submitting reports
- Add a teacher page for reviewing reports
- Store report data in a SQLite database
- Keep the interface simple so the prototype stays easy to test

## Database Update

The prototype uses a local SQLite database instead of only storing reports in the browser while the page is open.

This change means reports can still be loaded again after the page is refreshed, as long as the Python server and `reports.db` file are used.

The database version adds:

- A Python backend server
- A SQLite `reports` table
- API routes for loading, creating, updating, and deleting reports
- A seeded test report for checking unusual report values

## End Users

The main end users are students who need to report school infrastructure issues.

The secondary users are school staff and maintenance workers who need to review, manage, and respond to reports.

## Main Features

- Submit a school infrastructure report
- Enter student name, location, issue type, priority, and description
- Validate required form fields
- Show an error message when required fields are missing
- Show a success message when a report is submitted
- Display reports on the teacher dashboard
- View report details on the teacher page
- Update report status on the teacher page
- Delete a report on the teacher page
- Show report status counts on the teacher page

## Technologies Used

- HTML
- CSS
- JavaScript
- Python
- SQLite

## How to Run the Prototype

### Easy Method

Double-click:

```text
START.bat
```

This starts the Python server and opens:

```text
http://127.0.0.1:8000/student
http://127.0.0.1:8000/teacher?key=teacher123
```

### Manual Method

1. Open the project folder.
2. Start the backend server:

```bash
py server.py
```

If `py` does not work, use:

```bash
python server.py
```

3. Open the student page:

```text
http://127.0.0.1:8000/student
```

4. Open the teacher page in another browser tab:

```text
http://127.0.0.1:8000/teacher?key=teacher123
```

5. Use the student page to submit a report.
6. Use the teacher page to view, update, or delete reports.

The `reports.db` file is created automatically when the server starts.

The teacher key is a simple prototype passcode. It separates teacher actions from the student page, but it is not a full login system.

## Project Structure

```text
school-report-system/
  School Report System Prototype.html
  teacher.html
  server.py
  START.bat
  OPEN_THIS.bat
  README.md
```

The main prototype files stay in the project root so the launcher and server paths remain simple.
