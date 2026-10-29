# DonorBridge — Blood Donor Directory

DonorBridge is a small Flask application for adding, viewing, searching, editing, and deleting volunteer blood donor records. It stores records in a Neon-hosted PostgreSQL database. It uses plain HTML, CSS, and Jinja2 templates; it does not include fictional seed records.

> This directory is not medical advice and does not verify a donor's eligibility. Only enter contact details when you have permission to store them.

## Project files

- `app.py` — Flask routes, input validation, and parameterized PostgreSQL queries.
- `.env` — Your private local settings. It is ignored by Git. Do not share or commit it.
- `.env.example` — A template showing which environment variables to configure; its database URL is only a placeholder.
- `.gitignore` — Keeps `.env`, virtual environments, and Python cache files out of Git.
- `requirements.txt` — Flask, Psycopg 3, and python-dotenv dependencies.
- `templates/base.html` — Shared page layout, stylesheet link, and flash messages.
- `templates/index.html` — Donor registration form, summary cards, filters, and donor table.
- `templates/edit.html` — Prefilled donor editing form.
- `static/style.css` — Responsive white-and-red styling.

## Requirements

- Python 3.10 or later
- A Neon account and PostgreSQL project
- PowerShell on Windows (commands below use PowerShell)

## 1. Create and activate a virtual environment

Open the `DonorBridge` folder in VS Code, then open its integrated PowerShell terminal. Run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts for this terminal session and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Install Python dependencies

With the virtual environment active, run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Create a Neon project and get its connection string

1. Sign in to [Neon](https://neon.tech/) and create a project.
2. In the Neon project dashboard, open **Connect** and select the database/branch shown for your project.
3. Copy the PostgreSQL connection string. Neon provides the host, database name, username, password, and SSL configuration.
4. Keep this value private. Do not paste it into source code, screenshots, or public chat.

The application creates the `donors` table automatically the first time it connects successfully. You do not need to run SQL manually.

## 4. Configure `.env`

The `.env` file is a local, ignored file. If it is missing, create it by copying the example:

```powershell
Copy-Item .env.example .env
```

Open `.env` in VS Code and replace the placeholder values:

```dotenv
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@YOUR_NEON_HOST/YOUR_DATABASE?sslmode=require
FLASK_SECRET_KEY=put-a-long-random-private-value-here
```

Keep the actual Neon connection string on one line. Do not wrap it in quotes unless your dotenv setup requires that for special characters. If the Neon password contains URL-reserved characters, use the correctly URL-encoded connection string supplied by Neon or URL-encode the password component. Never commit `.env`.

If `FLASK_SECRET_KEY` is blank or missing, the app uses a documented development-only fallback. Set a private random value before sharing or deploying the app.

## 5. Run the application

From the project folder, with the virtual environment activated, run:

```powershell
python app.py
```

Open <http://127.0.0.1:5000/> in a browser. Stop the local server with `Ctrl+C`.

The app does not claim that Neon is reachable until a database-backed request succeeds. If `.env` is not configured, the home page displays a clear configuration message instead of claiming the directory is empty.

## 6. Try the CRUD operations

- **Create:** Complete the registration form and select **Add donor**. The server validates the values and inserts a row in PostgreSQL.
- **Read:** The donor table displays the records retrieved from PostgreSQL. Summary cards count all records, not just the filtered results.
- **Search/filter:** Select a blood group, enter all or part of a city name, and select **Search**. Select **Reset filters** to show all donors again.
- **Update:** Select **Edit** for a record, change its fields (including availability), and select **Save changes**.
- **Delete:** Select **Delete** and confirm the browser prompt. The server deletes that record and redirects to the refreshed directory.

For a practical demonstration, enter fictional names and non-working example contact details only. Do not invent or publish real people's contact information.

## 7. Manual testing checklist

- [ ] Add a donor with valid values; see the success message and new table row.
- [ ] Refresh the page; confirm the record still appears.
- [ ] Display all records and verify the ID, name, blood group, city, contact, and availability columns.
- [ ] Filter by a blood group and verify only matching records appear.
- [ ] Search/filter by a city name (including a partial city name).
- [ ] Select **Reset filters** and verify the full list returns.
- [ ] Edit a donor's name or city; save and verify the table changes.
- [ ] Change availability to **Unavailable**; verify the badge and summary counts change.
- [ ] Change availability back to **Available** and verify it persists after refresh.
- [ ] Delete a donor, confirm the prompt, and verify the row is gone after redirect/refresh.
- [ ] Submit empty or invalid required values; verify an error message appears and no invalid row is added.
- [ ] Check the Neon SQL Editor or table viewer after each change to verify data is stored in PostgreSQL.

## Troubleshooting

- **`DATABASE_URL is missing`:** Confirm `.env` is in the same project folder as `app.py`, and that the variable is spelled exactly `DATABASE_URL`.
- **Connection refused, timeout, or host lookup error:** Re-copy the current connection string from Neon, confirm network access, and make sure the Neon project/compute is available.
- **Password authentication failed:** Check that the username and password match the selected Neon database/branch. If credentials were reset, update `.env`.
- **SSL or certificate error:** Use the complete Neon connection string, including its SSL option (normally `sslmode=require`).
- **`ModuleNotFoundError`:** Activate `.venv` in the VS Code terminal and run `python -m pip install -r requirements.txt` with that same interpreter.
- **PowerShell does not allow activation:** Use the process-scoped execution policy command above; it applies only to the current terminal.
- **Changes do not appear:** Check for a success/error flash message and verify that the browser is using `http://127.0.0.1:5000/` and the same Neon database shown in `.env`.

## How the application works

Flask loads `.env` with `python-dotenv`. For each database operation, `app.py` reads `DATABASE_URL`, opens a Psycopg connection, creates the table if needed, and uses SQL placeholders (`%s`) for values. Connection and cursor context managers close resources and commit successful changes or roll back failed ones. The URL stays on the server and is never inserted into a template.

Routes:

| Route | Method | Operation |
| --- | --- | --- |
| `/` | GET | Read donor records, apply blood-group/city filters, and calculate summary counts |
| `/add` | POST | Validate and insert a donor |
| `/edit/<donor_id>` | GET | Read one donor and show the prefilled edit form |
| `/edit/<donor_id>` | POST | Validate and update that donor |
| `/delete/<donor_id>` | POST | Delete the selected donor |

## Viva questions and short answers

1. **What is Flask?** — Flask is a lightweight Python web framework for building web applications.
2. **What is PostgreSQL?** — PostgreSQL is a relational database that stores structured records in tables.
3. **What is Neon?** — Neon is a cloud-hosted PostgreSQL service.
4. **What does CRUD mean?** — Create, Read, Update, and Delete.
5. **What is Psycopg?** — Psycopg is the PostgreSQL adapter used by Python to connect to PostgreSQL and execute SQL.
6. **Why is `DATABASE_URL` stored in `.env`?** — It keeps private connection configuration outside the application source code.
7. **Why is `.env` in `.gitignore`?** — So private credentials are not accidentally committed to Git.
8. **What are parameterized SQL queries?** — Queries that pass values separately from SQL text, reducing SQL injection risk.
9. **What is Jinja2?** — The template engine Flask uses to render HTML with server-side data.
10. **What does `@app.get("/")` do?** — It registers a Flask view to handle GET requests to the home page.
11. **Why use POST for deleting a donor?** — Deletion changes server data, so it should not be triggered by a simple page link/GET request.
12. **What does `CREATE TABLE IF NOT EXISTS` do?** — It creates the table only when it does not already exist.
13. **What is a primary key?** — A column that uniquely identifies each row; here, it is the donor `id`.
14. **Why use flash messages?** — They provide short success or error feedback after a request.
15. **Does this application verify medical eligibility?** — No. It is only a donor directory and makes no medical eligibility assessment.
