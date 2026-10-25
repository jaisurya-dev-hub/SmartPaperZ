# SmartPaperZ
# SmartPaperZ

Previous-year question papers for colleges and government exams. Flask + SQLite + vanilla JS.

## Setup (Windows, PowerShell)
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then set SECRET_KEY (also set it in your shell: $env:SECRET_KEY="...")
python init_db.py
flask --app app create-admin
python app.py
```
Open http://127.0.0.1:5000. Admin login: http://127.0.0.1:5000/admin/login

## Tests
`python -m pytest -q`

## Uploading the first real TNPSC Group 4 paper
Log in as admin, open **Submit**, choose category *Competitive Exam*, exam *TNPSC Group 4*, add year, subject
(General Studies / General Tamil), language, and either the PDF or the official TNPSC source URL. Admin uploads publish immediately.
No papers are seeded; the exam directory is only a list of exams.

## Notes and limits
- Password reset by email is not implemented (no mail setup). Admins can suspend users; reset requires a DB edit.
- Rate limiting is in-memory (resets on restart, per process). Use a proper store in production.
- Backup: copy `smartpaperz.db` and the `uploads/` folder together while the app is stopped. Restore by copying them back.
- Before deploying: set a strong SECRET_KEY, SESSION_COOKIE_SECURE=1 behind HTTPS, use gunicorn/waitress, and run a security review.
