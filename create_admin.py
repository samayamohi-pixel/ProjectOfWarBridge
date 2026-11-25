from getpass import getpass

from werkzeug.security import generate_password_hash

from app import app, get_db, init_db, utcnow


def main():
    name = input("Administrator username: ").strip()
    email = input("Administrator email: ").strip().lower()
    password = getpass("Password (minimum 12 characters): ")
    confirmation = getpass("Confirm password: ")

    if not name or not email or len(password) < 12:
        raise SystemExit("Username, email, and a password of at least 12 characters are required.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    with app.app_context():
        init_db()
        db = get_db()
        if db.execute("SELECT id FROM users WHERE LOWER(email)=?", (email,)).fetchone():
            raise SystemExit("An account already exists for that email.")
        if db.execute(
            "SELECT id FROM users WHERE role='ADMIN' AND LOWER(name)=LOWER(?)",
            (name,),
        ).fetchone():
            raise SystemExit("An administrator already exists with that username.")
        db.execute(
            """INSERT INTO users(name,email,password_hash,role,verified,created_at)
               VALUES(?,?,?,'ADMIN',1,?)""",
            (name, email, generate_password_hash(password), utcnow()),
        )
        db.commit()
    print("Administrator account created. Sign in with the username or email you provided.")


if __name__ == "__main__":
    main()
