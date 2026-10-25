# PROJECT_STATUS

## Done (tests: 8 passed)
Schema + seed (exams, 5 colleges, no papers), auth (hashed passwords, sessions, CSRF, login throttle), admin login/dashboard
(approve/reject papers and colleges, feature, delete, reports, suspend users, audit log), paper search/filter/sort/paginate,
paper pages (/papers/<id>), PDF view/download/share, uploads (magic-byte check, uuid names, SHA-256 duplicate check, 15 MB cap),
college suggestion, bookmarks, reports, error pages, security headers, README.

## Not done yet (next steps, in order)
1. Admin forms to add/edit colleges, exams and papers (edit title/metadata) with search/pagination on admin tables.
2. Real TNPSC Group 4 records: find official PDFs/URLs at tnpsc.gov.in, verify, upload via admin (none seeded on purpose).
3. College page filters for department/course lists; exam page grouping by year.
4. Dark-mode toggle button (currently follows OS setting), separate static/js/search.js if needed.
5. Password reset (needs SMTP), mobile visual pass in a real browser, more tests (suspended users, pagination).

## Resume
Open this folder, read this file, run `python -m pytest -q`, then continue from "Not done yet" item 1.
