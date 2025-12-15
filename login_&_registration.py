import sqlite3
import hashlib
import re

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect(":memory:")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('Admin','Organizer','Consumer')) NOT NULL,
    organization TEXT
)
""")

# ---------------- PASSWORD HASHING ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- VALIDATORS ----------------
def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)

def is_valid_password(password):
    if len(password) < 6:
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False
    return True

# ---------------- INSERT DEFAULT ADMIN ----------------
cursor.execute("""
INSERT INTO users (user_id, name, phone, email, password_hash, role)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    "admin",
    "SystemAdmin",
    "9876543210",
    "admin@gmail.com",
    hash_password("Admin@123"),
    "Admin"
))
conn.commit()

# ---------------- REGISTRATION ----------------
def register_user():
    print("\n--- REGISTRATION ---")
    role = input("Register as (Consumer / Organizer): ").strip().title()

    if role not in ("Consumer", "Organizer"):
        print("❌ Invalid role")
        return

    # ---- Name (Immediate validation) ----
    while True:
        name = input("Enter Full Name: ").strip()
        if not name:
            print("❌ Name cannot be empty")
            continue
        cursor.execute("SELECT 1 FROM users WHERE name = ?", (name,))
        if cursor.fetchone():
            print("❌ Name already exists")
        else:
            break

    # ---- Phone (Immediate validation) ----
    while True:
        phone = input("Enter Phone Number: ").strip()
        if not is_valid_phone(phone):
            print("❌ Phone number must be exactly 10 digits")
            continue
        cursor.execute("SELECT 1 FROM users WHERE phone = ?", (phone,))
        if cursor.fetchone():
            print("❌ Phone number already registered")
        else:
            break

    # ---- Email (Immediate validation) ----
    while True:
        email = input("Enter Email: ").strip()
        if not is_valid_email(email):
            print("❌ Invalid email format")
            continue
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print("❌ Email already registered")
        else:
            break

    # ---- Password (Immediate validation) ----
    while True:
        password = input("Enter Password: ").strip()
        if not is_valid_password(password):
            print("❌ Password must contain:")
            print("   - 1 lowercase letter")
            print("   - 1 uppercase letter")
            print("   - 1 special character")
            print("   - Minimum 6 characters")
            continue
        confirm_password = input("Confirm Password: ").strip()
        if password != confirm_password:
            print("❌ Passwords do not match")
        else:
            break

    organization = None
    if role == "Organizer":
        while True:
            organization = input("Enter Organization Name: ").strip()
            if organization:
                break
            print("❌ Organization name is required")

    user_id = email

    cursor.execute("""
        INSERT INTO users
        (user_id, name, phone, email, password_hash, role, organization)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        phone,
        email,
        hash_password(password),
        role,
        organization
    ))
    conn.commit()

    print("✅ Registration successful")

# ---------------- LOGIN ----------------
def login():
    print("\n--- LOGIN ---")
    identifier = input("Enter Email / Phone / User ID: ").strip()
    password = input("Enter Password: ").strip()

    cursor.execute("""
        SELECT user_id, name, password_hash, role
        FROM users
        WHERE user_id = ?
           OR phone = ?
           OR email = ?
    """, (identifier, identifier, identifier))

    record = cursor.fetchone()

    if not record:
        print("❌ User not found")
        return None

    user_id, name, stored_hash, role = record

    if stored_hash != hash_password(password):
        print("❌ Invalid password")
        return None

    print(f"✅ Login successful ({role})")
    return {"user_id": user_id, "name": name, "role": role}

# ---------------- DASHBOARD ----------------
def dashboard(session):
    print("\n==============================")
    print("Welcome :", session["name"])
    print("Role    :", session["role"])
    print("==============================")

    if session["role"] == "Admin":
        print("1. Manage Locations")
        print("2. Approve Events")
    elif session["role"] == "Organizer":
        print("1. Create / Edit Events")
        print("2. Submit for Approval")
    else:
        print("1. Browse Events")
        print("2. Book Tickets")

    print("0. Logout")

# ---------------- MAIN ----------------
while True:
    print("\n===== EVENT MANAGEMENT SYSTEM =====")
    print("1. Register")
    print("2. Login")
    print("0. Exit")

    choice = input("Choose option: ")

    if choice == "1":
        register_user()
    elif choice == "2":
        session = login()
        if session:
            while True:
                dashboard(session)
                if input("Enter option: ") == "0":
                    print("🔒 Logged out")
                    break
    elif choice == "0":
        print("👋 Application closed")
        break
    else:
        print("❌ Invalid choice")
