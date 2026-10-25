import os, re, uuid, hashlib, secrets
from functools import wraps
import click
from flask import (Flask, render_template, request, redirect, url_for, session, flash, abort, g,
                   send_from_directory)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from app_utils import EMAIL, norm, throttled, hit
import db, seed_data

PER_PAGE = 12
CATEGORIES = ["School", "College", "Competitive Exam"]
SELECT = ("SELECT p.*, c.name AS college, e.name AS exam FROM papers p "
          "LEFT JOIN colleges c ON c.id=p.college_id LEFT JOIN exams e ON e.id=p.exam_id")

def create_user(name, email, pw, role="user"):
    return db.run("INSERT INTO users(name,email,pw_hash,role) VALUES(?,?,?,?)",
                  name, email.lower(), generate_password_hash(pw), role)

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config: app.config.update(config)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    db.init_app(app)

    @app.before_request
    def load_user():
        g.user = None
        if session.get("uid"):
            g.user = db.one("SELECT * FROM users WHERE id=? AND active=1", session["uid"])
            if not g.user: session.clear()
        if request.method == "POST" and not secrets.compare_digest(
                request.form.get("csrf", ""), session.get("csrf", "\0")):
            abort(400)

    @app.context_processor
    def inject():
        session.setdefault("csrf", secrets.token_hex(16))
        return dict(csrf=session["csrf"], user=g.user, CATEGORIES=CATEGORIES)

    @app.after_request
    def headers(r):
        r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "same-origin",
            "Content-Security-Policy": "default-src 'self'; frame-src 'self'; object-src 'self'"})
        return r

    def login_required(f):
        @wraps(f)
        def w(*a, **k):
            if not g.user: return redirect(url_for("login", next=request.path))
            return f(*a, **k)
        return w

    def admin_required(f):
        @wraps(f)
        def w(*a, **k):
            if not g.user: return redirect(url_for("admin_login"))
            if g.user["role"] != "admin": abort(403)
            return f(*a, **k)
        return w

    def log(action): db.run("INSERT INTO admin_log(admin_id,action) VALUES(?,?)", g.user["id"], action)

    def search(args, **fixed):
        w, a = ["p.status='approved'"], []
        qs = args.get("q", "").strip()
        if qs:
            w.append("(p.title LIKE ? OR p.subject LIKE ? OR p.course LIKE ? OR c.name LIKE ? OR e.name LIKE ?)")
            a += [f"%{qs}%"] * 5
        f = {k: args.get(k, "").strip() for k in ("category", "language", "year", "semester", "subject", "course")}
        f.update(fixed)
        for k, v in f.items():
            if v: w.append(f"p.{k}=? COLLATE NOCASE"); a.append(v)
        order = {"year": "p.year DESC, p.id DESC", "popular": "p.downloads DESC"}.get(args.get("sort"), "p.id DESC")
        page = max(1, request.args.get("page", 1, type=int))
        where = " WHERE " + " AND ".join(w)
        total = db.one("SELECT COUNT(*) n FROM papers p LEFT JOIN colleges c ON c.id=p.college_id "
                       "LEFT JOIN exams e ON e.id=p.exam_id" + where, *a)["n"]
        rows = db.q(SELECT + where + f" ORDER BY {order} LIMIT ? OFFSET ?", *a, PER_PAGE, (page - 1) * PER_PAGE)
        return dict(papers=rows, total=total, page=page, pages=max(1, -(-total // PER_PAGE)),
                    args={k: v for k, v in args.items() if k != "page"})

    def visible_paper(pid):
        p = db.one("SELECT * FROM papers WHERE id=?", pid)
        if not p: abort(404)
        if p["status"] != "approved" and not (g.user and (g.user["role"] == "admin" or g.user["id"] == p["uploader_id"])):
            abort(404)
        return p

    # ---------- public ----------
    @app.route("/")
    def index():
        n = lambda sql: db.one(sql)["n"]
        stats = dict(papers=n("SELECT COUNT(*) n FROM papers WHERE status='approved'"),
                     colleges=n("SELECT COUNT(*) n FROM colleges WHERE status='approved'"),
                     exams=n("SELECT COUNT(*) n FROM exams"),
                     downloads=n("SELECT COALESCE(SUM(downloads),0) n FROM papers"))
        return render_template("index.html", stats=stats,
            recent=db.q(SELECT + " WHERE p.status='approved' ORDER BY p.featured DESC, p.id DESC LIMIT 6"),
            exams=db.q("SELECT e.*, (SELECT COUNT(*) FROM papers p WHERE p.exam_id=e.id AND p.status='approved') n "
                       "FROM exams e ORDER BY n DESC, name LIMIT 8"),
            colleges=db.q("SELECT * FROM colleges WHERE status='approved' ORDER BY name LIMIT 6"))

    @app.route("/page/<slug>")
    def page(slug):
        pages = {"about": "About SmartPaperZ", "contact": "Contact", "privacy": "Privacy Policy", "terms": "Terms"}
        if slug not in pages: abort(404)
        return render_template("page.html", title=pages[slug], slug=slug)

    @app.route("/papers")
    def papers():
        return render_template("papers.html", heading="All question papers", **search(request.args))

    @app.route("/papers/<int:pid>")
    def paper_detail(pid):
        p = visible_paper(pid)
        full = db.one(SELECT + " WHERE p.id=?", pid)
        saved = g.user and db.one("SELECT 1 FROM bookmarks WHERE user_id=? AND paper_id=?", g.user["id"], pid)
        return render_template("paper_detail.html", p=full, saved=saved)

    def send_pdf(pid, attach):
        p = visible_paper(pid)
        if not p["stored_name"]: abort(404)
        if attach: db.run("UPDATE papers SET downloads=downloads+1 WHERE id=?", pid)
        return send_from_directory(app.config["UPLOAD_FOLDER"], p["stored_name"], mimetype="application/pdf",
                                   as_attachment=attach, download_name=(secure_filename(p["title"]) or "paper") + ".pdf")

    @app.route("/papers/<int:pid>/file")
    def paper_file(pid): return send_pdf(pid, False)

    @app.route("/papers/<int:pid>/download")
    def paper_download(pid): return send_pdf(pid, True)

    @app.route("/colleges")
    def colleges():
        st, qs = request.args.get("state", ""), request.args.get("q", "").strip()
        w, a = ["status='approved'"], []
        if st: w.append("state=?"); a.append(st)
        if qs: w.append("name LIKE ?"); a.append(f"%{qs}%")
        rows = db.q("SELECT c.*, (SELECT COUNT(*) FROM papers p WHERE p.college_id=c.id AND p.status='approved') n "
                    "FROM colleges c WHERE " + " AND ".join(w) + " ORDER BY name", *a)
        states = [r["state"] for r in db.q("SELECT DISTINCT state FROM colleges WHERE status='approved' ORDER BY state")]
        return render_template("colleges.html", rows=rows, states=states, st=st, q=qs)

    @app.route("/colleges/<int:cid>")
    def college_detail(cid):
        c = db.one("SELECT * FROM colleges WHERE id=? AND status='approved'", cid) or abort(404)
        return render_template("papers.html", heading=c["name"],
            sub=", ".join(x for x in (c["city"], c["state"], c["university"]) if x), **search(request.args, college_id=cid))

    @app.route("/exams")
    def exams():
        qs = request.args.get("q", "").strip()
        rows = db.q("SELECT e.*, (SELECT COUNT(*) FROM papers p WHERE p.exam_id=e.id AND p.status='approved') n "
                    "FROM exams e WHERE e.name LIKE ? ORDER BY category, name", f"%{qs}%")
        return render_template("exams.html", rows=rows, q=qs)

    @app.route("/exams/<int:eid>")
    def exam_detail(eid):
        e = db.one("SELECT * FROM exams WHERE id=?", eid) or abort(404)
        return render_template("papers.html", heading=e["name"], sub=f"{e['category']} · {e['body'] or ''}",
                               **search(request.args, exam_id=eid))

    # ---------- accounts ----------
    def do_login(admin):
        key = "login:" + (request.remote_addr or "?")
        if request.method == "POST":
            if throttled(key): flash("Too many attempts. Try again in a few minutes.", "error")
            else:
                u = db.one("SELECT * FROM users WHERE email=? AND active=1", request.form.get("email", "").lower().strip())
                if u and check_password_hash(u["pw_hash"], request.form.get("password", "")) and (u["role"] == "admin" or not admin):
                    session.clear(); session["uid"] = u["id"]
                    nxt = request.args.get("next", "")
                    return redirect(url_for("admin") if admin else nxt if nxt.startswith("/") and not nxt.startswith("//") else url_for("index"))
                hit(key); flash("Email or password is incorrect.", "error")
        return render_template("auth.html", mode="admin" if admin else "login")

    @app.route("/login", methods=["GET", "POST"])
    def login(): return do_login(False)

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login(): return do_login(True)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            n, em, pw = request.form.get("name", "").strip(), request.form.get("email", "").lower().strip(), request.form.get("password", "")
            err = ("Enter your name." if not n else "Enter a valid email." if not EMAIL.match(em)
                   else "Password needs at least 8 characters." if len(pw) < 8
                   else "That email is already registered." if db.one("SELECT 1 FROM users WHERE email=?", em) else None)
            if err: flash(err, "error")
            else:
                session.clear(); session["uid"] = create_user(n, em, pw)
                return redirect(url_for("index"))
        return render_template("auth.html", mode="register")

    @app.post("/logout")
    def logout(): session.clear(); return redirect(url_for("index"))

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html", mine=db.q(SELECT + " WHERE p.uploader_id=? ORDER BY p.id DESC", g.user["id"]))

    @app.route("/bookmarks")
    @login_required
    def bookmarks():
        rows = db.q(SELECT + " JOIN bookmarks b ON b.paper_id=p.id WHERE b.user_id=? AND p.status='approved'", g.user["id"])
        return render_template("papers.html", heading="Saved papers", papers=rows, total=len(rows), page=1, pages=1, args={})

    @app.post("/bookmark/<int:pid>")
    @login_required
    def bookmark(pid):
        visible_paper(pid)
        if db.one("SELECT 1 FROM bookmarks WHERE user_id=? AND paper_id=?", g.user["id"], pid):
            db.run("DELETE FROM bookmarks WHERE user_id=? AND paper_id=?", g.user["id"], pid)
        else: db.run("INSERT INTO bookmarks VALUES(?,?)", g.user["id"], pid)
        return redirect(url_for("paper_detail", pid=pid))

    @app.post("/report/<int:pid>")
    @login_required
    def report(pid):
        visible_paper(pid)
        reason = request.form.get("reason", "").strip()[:500]
        if reason:
            db.run("INSERT INTO reports(paper_id,user_id,reason) VALUES(?,?,?)", pid, g.user["id"], reason)
            flash("Thanks. An administrator will review this paper.", "ok")
        else: flash("Tell us what is wrong with this paper.", "error")
        return redirect(url_for("paper_detail", pid=pid))

    # ---------- submission ----------
    @app.route("/submit", methods=["GET", "POST"])
    @login_required
    def submit():
        ctx = dict(colleges=db.q("SELECT id,name,state FROM colleges WHERE status='approved' ORDER BY name"),
                   exams=db.q("SELECT id,name FROM exams ORDER BY name"))
        if request.method == "GET": return render_template("submit.html", f={}, **ctx)
        f, file, err = request.form, request.files.get("pdf"), []
        title, cat, url, year = f.get("title", "").strip(), f.get("category"), f.get("source_url", "").strip(), f.get("year", type=int)
        if not title: err.append("Title is required.")
        if cat not in CATEGORIES: err.append("Choose a category.")
        if f.get("year") and (year is None or not 1950 <= year <= 2100): err.append("Enter a valid year.")
        if url and not re.match(r"^https?://", url): err.append("Source URL must start with http:// or https://.")
        data = None
        if file and file.filename:
            data = file.read()
            if not data.startswith(b"%PDF-"): err.append("That file is not a valid PDF.")
        elif not url: err.append("Attach a PDF or give a source URL.")
        sha = hashlib.sha256(data).hexdigest() if data else None
        if sha and db.one("SELECT 1 FROM papers WHERE sha256=?", sha): err.append("This PDF has already been submitted.")
        if err:
            for e in err: flash(e, "error")
            return render_template("submit.html", f=f, **ctx), 400
        admin = g.user["role"] == "admin"
        cid, eid = f.get("college_id", type=int) or None, f.get("exam_id", type=int) or None
        nc, ns = f.get("new_college", "").strip(), f.get("new_state", "").strip()
        if nc and ns:
            ex = db.one("SELECT id FROM colleges WHERE norm=? AND state=?", norm(nc), ns)
            cid = ex["id"] if ex else db.run("INSERT INTO colleges(name,norm,state,status) VALUES(?,?,?,?)",
                                             nc, norm(nc), ns, "approved" if admin else "pending")
        stored = None
        if data:
            stored = uuid.uuid4().hex + ".pdf"
            with open(os.path.join(app.config["UPLOAD_FOLDER"], stored), "wb") as fh: fh.write(data)
        pid = db.run("INSERT INTO papers(title,category,college_id,exam_id,course,subject,year,semester,language,stage,description,"
                     "stored_name,sha256,source_url,status,uploader_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     title, cat, cid, eid, f.get("course"), f.get("subject"), year, f.get("semester"), f.get("language"),
                     f.get("stage"), f.get("description"), stored, sha, url or None, "approved" if admin else "pending", g.user["id"])
        flash("Paper published." if admin else "Thanks. Your paper is waiting for review.", "ok")
        return redirect(url_for("paper_detail", pid=pid))

    # ---------- admin ----------
    @app.route("/admin")
    @admin_required
    def admin():
        n = lambda sql: db.one(sql)["n"]
        stats = dict(papers=n("SELECT COUNT(*) n FROM papers WHERE status='approved'"), users=n("SELECT COUNT(*) n FROM users"),
                     colleges=n("SELECT COUNT(*) n FROM colleges WHERE status='approved'"),
                     pending=n("SELECT COUNT(*) n FROM papers WHERE status='pending'"),
                     downloads=n("SELECT COALESCE(SUM(downloads),0) n FROM papers"))
        return render_template("admin.html", stats=stats,
            pending=db.q(SELECT + " WHERE p.status='pending' ORDER BY p.id"),
            allp=db.q(SELECT + " ORDER BY p.id DESC LIMIT 50"),
            pcolleges=db.q("SELECT * FROM colleges WHERE status='pending'"),
            reports=db.q("SELECT r.*, p.title, u.email FROM reports r JOIN papers p ON p.id=r.paper_id "
                         "JOIN users u ON u.id=r.user_id WHERE r.status='open'"),
            users=db.q("SELECT * FROM users ORDER BY id DESC LIMIT 50"))

    @app.post("/admin/paper/<int:pid>/<act>")
    @admin_required
    def admin_paper(pid, act):
        p = db.one("SELECT * FROM papers WHERE id=?", pid) or abort(404)
        if act in ("approve", "reject"):
            db.run("UPDATE papers SET status=? WHERE id=?", "approved" if act == "approve" else "rejected", pid)
        elif act == "feature": db.run("UPDATE papers SET featured=1-featured WHERE id=?", pid)
        elif act == "delete":
            if p["stored_name"]:
                try: os.remove(os.path.join(app.config["UPLOAD_FOLDER"], p["stored_name"]))
                except OSError: pass
            db.run("DELETE FROM papers WHERE id=?", pid)
        else: abort(404)
        log(f"paper {pid} {act}"); return redirect(url_for("admin"))

    @app.post("/admin/college/<int:cid>/<act>")
    @admin_required
    def admin_college(cid, act):
        if act not in ("approve", "reject"): abort(404)
        db.run("UPDATE colleges SET status=? WHERE id=?", "approved" if act == "approve" else "rejected", cid)
        log(f"college {cid} {act}"); return redirect(url_for("admin"))

    @app.post("/admin/report/<int:rid>/<act>")
    @admin_required
    def admin_report(rid, act):
        r = db.one("SELECT * FROM reports WHERE id=?", rid) or abort(404)
        if act == "remove": db.run("UPDATE papers SET status='removed' WHERE id=?", r["paper_id"])
        elif act != "dismiss": abort(404)
        db.run("UPDATE reports SET status=? WHERE id=?", "actioned" if act == "remove" else "dismissed", rid)
        log(f"report {rid} {act}"); return redirect(url_for("admin"))

    @app.post("/admin/user/<int:uid>/toggle")
    @admin_required
    def admin_user(uid):
        if uid == g.user["id"]: abort(400)
        db.run("UPDATE users SET active=1-active WHERE id=?", uid); log(f"user {uid} toggle")
        return redirect(url_for("admin"))

    # ---------- errors & CLI ----------
    for code, msg in {400: "That request could not be processed.", 403: "You do not have access to this page.",
                      404: "We could not find that page or paper.", 413: "That file is too large (15 MB maximum).",
                      500: "Something went wrong on our side."}.items():
        app.register_error_handler(code, lambda e, c=code, m=msg: (render_template("error.html", code=c, msg=m), c))

    @app.cli.command("init-db")
    def _init(): db.init_db(); seed_data.seed(); click.echo("Database ready.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt=True)
    @click.option("--email", prompt=True)
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def _admin(name, email, password):
        if len(password) < 8: raise click.ClickException("Password needs at least 8 characters.")
        create_user(name, email, password, "admin"); click.echo("Administrator created.")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
