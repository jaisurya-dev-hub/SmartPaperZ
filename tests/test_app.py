import io, os, sys, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app, create_user
import db, seed_data

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"

@pytest.fixture
def c(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db"), "UPLOAD_FOLDER": str(tmp_path / "up")})
    with app.app_context():
        db.init_db(); seed_data.seed()
        create_user("Admin", "admin@x.com", "adminpass1", "admin")
    cl = app.test_client(); cl.app = app
    return cl

def post(c, url, **d):
    with c.session_transaction() as s: s["csrf"] = "t"
    return c.post(url, data=dict(csrf="t", **d))

def login(c, email, pw, url="/login"): return post(c, url, email=email, password=pw)

def upload(c, name="Maths 2023", pdf=PDF, fname="a.pdf", **extra):
    return post(c, "/submit", title=name, category="College", year="2023", subject="Maths",
                pdf=(io.BytesIO(pdf), fname), **extra)

def test_db_init_and_seed(c):
    with c.application.app_context():
        assert db.one("SELECT COUNT(*) n FROM exams")["n"] >= 15
        assert db.one("PRAGMA foreign_keys")[0] == 1

def test_register_login_and_bad_password(c):
    assert post(c, "/register", name="A", email="a@x.com", password="longenough").status_code == 302
    post(c, "/logout")
    assert login(c, "a@x.com", "wrongpass").status_code == 200
    assert login(c, "a@x.com", "longenough").status_code == 302
    assert post(c, "/register", name="B", email="b@x.com", password="short").status_code == 200

def test_csrf_required(c):
    assert c.post("/login", data={"email": "a", "password": "b"}).status_code == 400

def test_admin_authorization(c):
    assert c.get("/admin").status_code == 302
    post(c, "/register", name="U", email="u@x.com", password="longenough")
    assert c.get("/admin").status_code == 403
    assert post(c, "/admin/paper/1/approve").status_code == 403
    assert login(c, "u@x.com", "longenough", "/admin/login").status_code == 200
    post(c, "/logout"); assert login(c, "admin@x.com", "adminpass1", "/admin/login").status_code == 302
    assert c.get("/admin").status_code == 200

def test_upload_review_share_download(c):
    post(c, "/register", name="U", email="u@x.com", password="longenough")
    assert upload(c).status_code == 302
    post(c, "/logout")
    assert c.get("/papers/1").status_code == 404 and c.get("/papers/1/download").status_code == 404
    assert b"Maths 2023" not in c.get("/papers").data
    login(c, "admin@x.com", "adminpass1", "/admin/login")
    assert post(c, "/admin/paper/1/approve").status_code == 302
    post(c, "/logout")
    assert b"Maths 2023" in c.get("/papers?q=maths&year=2023").data
    assert c.get("/papers/1").status_code == 200
    r = c.get("/papers/1/download"); assert r.status_code == 200 and r.data.startswith(b"%PDF-")
    assert b"Maths 2023" not in c.get("/papers?year=1999").data

def test_invalid_uploads(c):
    post(c, "/register", name="U", email="u@x.com", password="longenough")
    assert upload(c, pdf=b"MZ not a pdf", fname="evil.pdf").status_code == 400
    assert upload(c).status_code == 302
    assert upload(c, name="Dup").status_code == 400
    assert post(c, "/submit", title="", category="x").status_code == 400

def test_missing_and_empty_states(c):
    assert c.get("/papers/999").status_code == 404 and b"could not find" in c.get("/papers/999").data
    assert b"No papers here yet" in c.get("/exams/1").data
    assert c.get("/exams/9999").status_code == 404

def test_suggest_college_and_reports(c):
    post(c, "/register", name="U", email="u@x.com", password="longenough")
    upload(c, new_college="Test Arts College", new_state="Kerala")
    with c.application.app_context():
        assert db.one("SELECT status FROM colleges WHERE name='Test Arts College'")["status"] == "pending"
    assert post(c, "/report/1", reason="duplicate").status_code == 302
    post(c, "/logout"); login(c, "admin@x.com", "adminpass1", "/admin/login")
    assert b"duplicate" in c.get("/admin").data
    assert post(c, "/admin/report/1/remove").status_code == 302
    assert c.get("/papers/1").status_code == 200  # admin may still see removed paper
