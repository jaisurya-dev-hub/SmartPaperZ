"""Directory data only. No question papers are seeded: add real ones through the admin upload."""
import db
from app_utils import norm

EXAMS = [
 ("TNPSC Group 4","State PSC","TNPSC"),("TNPSC Group 2 / 2A","State PSC","TNPSC"),("TNPSC Group 1","State PSC","TNPSC"),
 ("TNUSRB Police Constable","State PSC","TNUSRB"),("TN TRB Teachers Recruitment","Teaching","TN TRB"),
 ("UPSC Civil Services Examination","Civil Services","UPSC"),("SSC CGL","SSC","SSC"),("SSC CHSL","SSC","SSC"),("SSC MTS","SSC","SSC"),
 ("RRB NTPC","Railways","RRB"),("RRB Group D","Railways","RRB"),("IBPS PO","Banking","IBPS"),("IBPS Clerk","Banking","IBPS"),
 ("SBI PO","Banking","SBI"),("SBI Clerk","Banking","SBI"),("CTET","Teaching","CBSE"),
]
COLLEGES = [
 ("Anna University","Tamil Nadu","Chennai",None),("University of Madras","Tamil Nadu","Chennai",None),
 ("IIT Madras","Tamil Nadu","Chennai",None),("PSG College of Technology","Tamil Nadu","Coimbatore","Anna University"),
 ("Loyola College","Tamil Nadu","Chennai","University of Madras"),
]

def seed():
    for n, c, b in EXAMS:
        db.run("INSERT OR IGNORE INTO exams(name,category,body) VALUES(?,?,?)", n, c, b)
    for n, s, city, u in COLLEGES:
        db.run("INSERT OR IGNORE INTO colleges(name,norm,state,city,university,status) VALUES(?,?,?,?,?,'approved')",
               n, norm(n), s, city, u)
