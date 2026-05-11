# BrokenPortal

A deliberately vulnerable web application built with Python and Flask for cybersecurity coursework. It contains four intentional vulnerabilities that demonstrate real-world attack classes in a controlled, isolated environment. This project is for educational use only and must never be deployed on a public-facing server.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Setup and Installation](#setup-and-installation)
5. [Default Credentials](#default-credentials)
6. [Vulnerability Reference](#vulnerability-reference)
   - [1. SQL Injection](#1-sql-injection)
   - [2. Insecure Direct Object Reference (IDOR)](#2-insecure-direct-object-reference-idor)
   - [3. Path Traversal](#3-path-traversal)
   - [4. Unrestricted File Upload](#4-unrestricted-file-upload)
7. [Database Schema](#database-schema)
8. [Routes Reference](#routes-reference)
9. [Legal Disclaimer](#legal-disclaimer)

---

## Project Overview

BrokenPortal is a multi-page web application that simulates a corporate internal portal. It was designed for a university cybersecurity principles course project. The application mimics the visual style of professional security training platforms and presents each vulnerability as a self-contained lab module with contextual hints and realistic data.

The goal is not just to show that vulnerabilities exist, but to let a tester manually reproduce, understand, and document each exploit from scratch using only a browser or tools like Burp Suite.

---

## Technology Stack

| Component    | Technology                  |
|--------------|-----------------------------|
| Backend      | Python 3, Flask 3.0.3       |
| Database     | SQLite (file-based)         |
| Templating   | Jinja2 (via Flask)          |
| Frontend     | HTML, CSS (custom, no framework) |
| Session Mgmt | Flask server-side sessions  |
| File Storage | Local filesystem (`uploads/` folder) |

---

## Project Structure

```
broken-portal/
    app.py                  Entry point. All routes and business logic live here.
    database.db             Auto-generated SQLite database on first run.
    requirements.txt        Python dependencies (Flask only).
    uploads/                Directory where uploaded files are stored.
    static/
        style.css           All styling. PortSwigger Academy-inspired design.
    templates/
        base.html           Shared layout with navigation bar and footer.
        index.html          Landing page. Lists all four vulnerabilities.
        login.html          Login form. Vulnerable to SQL injection.
        dashboard.html      Post-login hub linking to each vulnerability lab.
        profile.html        User profile page. Vulnerable to IDOR.
        search.html         Document search. Vulnerable to SQL injection.
        upload.html         File upload page. No type or content restriction.
```

---

## Setup and Installation

**Requirements:** Python 3.8 or higher must be installed.

**Step 1.** Clone or extract the project folder.

**Step 2.** Install the only dependency:

```bash
pip install flask
```

**Step 3.** Start the application:

```bash
python app.py
```

**Step 4.** Open your browser and navigate to:

```
http://127.0.0.1:5000
```

The database is created automatically on first run and seeded with three user accounts and four documents. No migrations or setup scripts are required.

---

## Default Credentials

These accounts are inserted automatically when the database is first created.

| Username | Password  | Role          |
|----------|-----------|---------------|
| admin    | admin123  | administrator |
| wiener   | peter     | user          |
| carlos   | montoya   | user          |

All passwords are stored in **plaintext**. This is intentional and represents an additional weakness beyond the four primary vulnerabilities.

---

## Vulnerability Reference

### 1. SQL Injection

**Severity:** High
**CWE:** CWE-89 Improper Neutralization of Special Elements used in an SQL Command
**Affected Routes:** `/login` (POST), `/search` (GET)

**What is vulnerable:**
User input is inserted directly into SQL query strings using Python f-strings. No parameterized queries or input sanitization is used at any point.

The login route constructs its query like this:

```python
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
```

The search route constructs its query like this:

```python
sql = f"SELECT id,title,content FROM documents WHERE title LIKE '%{query}%'"
```

**How to exploit the login bypass:**

Enter the following in the username field and anything in the password field:

```
' OR '1'='1' --
```

This transforms the query into a condition that is always true and returns the first user record, logging you in as that user without knowing any valid password.

**How to exploit the search with a UNION attack:**

Enter the following in the search box to extract all usernames and passwords from the users table:

```
%' UNION SELECT 1,username,password FROM users --
```

Each row returned will display a username in the title field and its plaintext password in the content field.

To enumerate the database schema first:

```
%' UNION SELECT 1,2,sql FROM sqlite_master --
```

**Why it works:** Flask does not automatically escape SQL inputs. The developer is using raw string concatenation instead of the `?` placeholder syntax that SQLite3 provides for safe parameterized queries.

---

### 2. Insecure Direct Object Reference (IDOR)

**Severity:** Medium
**CWE:** CWE-284 Improper Access Control
**Affected Route:** `/profile` (GET)

**What is vulnerable:**
The profile page accepts a user-supplied `id` parameter in the URL and queries the database for that user record. There is no check to verify whether the currently logged-in session user owns or is authorized to view the requested account.

The vulnerable code:

```python
user_id = request.args.get('id', session.get('uid', 1))
user = c.execute(f"SELECT * FROM users WHERE id={user_id}").fetchone()
```

**How to exploit:**

After logging in as `wiener` (uid=2), modify the URL parameter:

```
http://127.0.0.1:5000/profile?id=1
```

This returns the full record for the admin account, including their plaintext password and role, without any authentication or authorization check.

Iterating through IDs 1, 2, and 3 will expose all three user accounts including the administrator.

The profile page also contains a next/previous navigation that makes this enumeration trivial.

**Why it works:** The server trusts the client to supply a valid, authorized ID. The session contains the logged-in user's real uid but it is never compared against the requested id.

---

### 3. Path Traversal

**Severity:** Medium
**CWE:** CWE-22 Improper Limitation of a Pathname to a Restricted Directory
**Affected Route:** `/image` (GET)

**What is vulnerable:**
The `/image` endpoint accepts a `file` query parameter and passes it directly to `os.path.join()` before calling `send_file()`. There is no validation that the resulting path stays within the `static/` directory.

The vulnerable code:

```python
filename = request.args.get('file', '')
path = os.path.join('static', filename)
return send_file(path)
```

**How to exploit:**

Read the application source code directly from the server:

```
http://127.0.0.1:5000/image?file=../app.py
```

Read the raw SQLite database file:

```
http://127.0.0.1:5000/image?file=../database.db
```

On Linux systems, read system files:

```
http://127.0.0.1:5000/image?file=../../etc/passwd
```

**Why it works:** `os.path.join('static', '../app.py')` resolves to `static/../app.py` which is equivalent to `app.py` in the working directory. Python does not block this traversal by default and Flask's `send_file()` will serve whatever valid file path it is given.

---

### 4. Unrestricted File Upload

**Severity:** High
**CWE:** CWE-434 Unrestricted Upload of File with Dangerous Type
**Affected Route:** `/upload` (POST), `/uploads/<filename>` (GET)

**What is vulnerable:**
The upload handler saves any file to the `uploads/` directory without checking the extension, MIME type, or file contents. The original filename is preserved as-is. Uploaded files are immediately accessible via a direct URL.

The vulnerable code:

```python
file = request.files.get('file')
filepath = os.path.join(UPLOAD_FOLDER, file.filename)
file.save(filepath)
```

**How to exploit:**

Create a file named `shell.php` containing a basic webshell payload, upload it through the form, then access it at:

```
http://127.0.0.1:5000/uploads/shell.php
```

Note: PHP execution requires a PHP-capable server. On this Python/Flask server the file will be served as raw text, which still confirms the upload restriction bypass.

For a more impactful demonstration within this Flask environment, upload a Python script and demonstrate that the content is accessible and unfiltered.

Additional bypass techniques the application does not defend against:

Double extension: `shell.php.jpg`
Null byte injection: `shell.php%00.jpg`
Uppercase extension: `shell.PHP`
Content-Type spoofing: set MIME type to `image/jpeg` while uploading a script

**Why it works:** There is no whitelist of allowed file types, no blacklist of dangerous extensions, no magic byte inspection, and no sandboxed execution environment for the upload directory.

---

## Database Schema

The database is auto-created at `database.db` in the project root on first run.

**users table**

| Column      | Type    | Notes                        |
|-------------|---------|------------------------------|
| id          | INTEGER | Primary key, auto-increment  |
| username    | TEXT    | Plaintext                    |
| password    | TEXT    | Plaintext, no hashing        |
| role        | TEXT    | Either `user` or `administrator` |
| profile_pic | TEXT    | Unused column, NULL by default |

**documents table**

| Column   | Type    | Notes                        |
|----------|---------|------------------------------|
| id       | INTEGER | Primary key, auto-increment  |
| title    | TEXT    | Searchable via `/search`     |
| content  | TEXT    | Displayed in search results  |
| owner_id | INTEGER | References users.id          |

---

## Routes Reference

| Method | Route                 | Auth Required | Vulnerability         |
|--------|-----------------------|---------------|-----------------------|
| GET    | `/`                   | No            | None                  |
| GET    | `/login`              | No            | None                  |
| POST   | `/login`              | No            | SQL Injection         |
| GET    | `/logout`             | No            | None                  |
| GET    | `/dashboard`          | Yes           | None                  |
| GET    | `/profile`            | No            | IDOR, SQL Injection   |
| GET    | `/search`             | No            | SQL Injection         |
| GET    | `/image`              | No            | Path Traversal        |
| GET    | `/upload`             | No            | None                  |
| POST   | `/upload`             | No            | Unrestricted Upload   |
| GET    | `/uploads/<filename>` | No            | Unrestricted Upload   |

Note: Authentication is enforced only on `/dashboard`. All other routes are accessible without a valid session, which is itself an access control weakness.

---

## Legal Disclaimer

This application is intentionally insecure. It was created solely for academic coursework in a controlled university environment. Running this application on a public network or any shared infrastructure is prohibited. The vulnerabilities demonstrated here are illegal to exploit against systems you do not own or have explicit written permission to test. The authors accept no liability for misuse.
