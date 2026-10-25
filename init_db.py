from app import create_app
import db, seed_data
app = create_app()
with app.app_context():
    db.init_db(); seed_data.seed()
print("Database ready.")
