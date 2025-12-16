
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

DB_PATH = "event_management.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        role TEXT,
        company_name TEXT,
        verified_status INTEGER
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS venues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue_name TEXT NOT NULL,
        address TEXT,
        city TEXT,
        pincode TEXT,
        amenities TEXT,
        capacity INTEGER NOT NULL,
        status INTEGER NOT NULL DEFAULT 1
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name TEXT NOT NULL,
        venue_id INTEGER NOT NULL,
        price REAL NOT NULL,
        status TEXT NOT NULL,
        occupancy INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        no_of_tickets INTEGER NOT NULL,
        payment_type TEXT NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    cur.execute("SELECT COUNT(*) AS c FROM users;")
    if cur.fetchone()["c"] == 0:
        cur.executemany("""
            INSERT INTO users (name, email, password, phone, role, company_name, verified_status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, [
            ("Karthick Ragav", "karthick@example.com", "pass123", "9876543210", "consumer", None, 1),
            ("Priya", "priya@example.com", "pass123", "9876500001", "consumer", None, 0),
            ("Event Admin", "admin@example.com", "admin123", "9999999999", "admin", "EM Admin LLC", 1),
            ("Organizer One", "org1@example.com", "org123", "8888888888", "organizer", "Chennai Events Pvt Ltd", 1),
        ])

    cur.execute("SELECT COUNT(*) AS c FROM venues;")
    if cur.fetchone()["c"] == 0:
        cur.executemany("""
            INSERT INTO venues (venue_name, address, city, pincode, amenities, capacity, status)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, [
            ("Chennai Trade Centre", "Nandambakkam", "Chennai", "600089", "Parking,AC", 100, 1),
            ("Marina Beach Arena", "Marina", "Chennai", "600013", "OpenAir,FoodStalls", 250, 1),
            ("IITM Research Park Auditorium", "Kanagam Road", "Chennai", "600113", "Parking,Projector,WiFi", 80, 1),
            ("Phoenix Marketcity Hall", "Velachery", "Chennai", "600042", "AC,Parking", 150, 1),
        ])

    cur.execute("SELECT COUNT(*) AS c FROM events;")
    if cur.fetchone()["c"] == 0:
        cur.executemany("""
            INSERT INTO events (event_name, venue_id, price, status, occupancy)
            VALUES (?, ?, ?, ?, ?);
        """, [
            ("Tech Meetup Chennai", 1, 299.0, "scheduled", 0),
            ("Music Fest", 2, 799.0, "scheduled", 0),
            ("Startup Pitch Day", 3, 499.0, "scheduled", 0),
            ("Art & Craft Expo", 4, 199.0, "scheduled", 0),
        ])

    conn.commit()
    conn.close()

def safe_int(prompt):
    val = input(prompt).strip()
    try:
        return int(val)
    except ValueError:
        return None

def get_event(conn, event_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT e.*, v.venue_name, v.city, v.capacity, v.pincode, v.amenities, v.status AS venue_status
        FROM events e
        JOIN venues v ON e.venue_id = v.id
        WHERE e.id = ?;
    """, (event_id,))
    return cur.fetchone()

def get_user(conn, user_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
    return cur.fetchone()

def get_user_by_credentials(conn, email, password):
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ? AND password = ?;", (email, password))
    return cur.fetchone()

def event_remaining_seats(conn, event_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT (v.capacity - e.occupancy) AS remaining
        FROM events e
        JOIN venues v ON e.venue_id = v.id
        WHERE e.id = ?;
    """, (event_id,))
    row = cur.fetchone()
    return row["remaining"] if row else None

def view_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.event_name, e.price, e.status, e.occupancy,
               v.venue_name, v.city, v.capacity, v.pincode, v.amenities, v.status AS venue_status,
               (v.capacity - e.occupancy) AS remaining
        FROM events e
        JOIN venues v ON e.venue_id = v.id
        ORDER BY e.status ASC, e.event_name ASC;
    """)
    rows = cur.fetchall()

    print("\nAvailable Events:")
    if not rows:
        print("No events found.")
    else:
        print("-" * 120)
        for e in rows:
            remaining = e["remaining"]
            venue_active = "Active" if e["venue_status"] else "Inactive"
            print(
                f"ID: {e['id']} | {e['event_name']} | Venue: {e['venue_name']} ({e['city']}, {e['pincode']}) | "
                f"Amenities: {e['amenities']} | Venue Status: {venue_active} | "
                f"Event Status: {e['status']} | Price: ₹{e['price']:.2f} | "
                f"Capacity: {e['capacity']} | Occupancy: {e['occupancy']} | Remaining: {remaining}"
            )
        print("-" * 120)
    conn.close()

def book_event(user_id):
    conn = get_connection()
    try:
        view_events()

        event_id = safe_int("\nEnter Event ID to book: ")
        if event_id is None:
            print("❌ Invalid event ID. Please enter a number.")
            return

        event = get_event(conn, event_id)
        if not event:
            print("❌ Event not found.")
            return

        if not event["venue_status"]:
            print("❌ Booking not allowed: venue is inactive.")
            return

        if event["status"].lower() in ("cancelled", "closed"):
            print(f"❌ Booking not allowed: event status is '{event['status']}'.")
            return

        remaining = event_remaining_seats(conn, event_id)
        if remaining is None:
            print("❌ Unable to compute remaining seats.")
            return

        tickets = safe_int("Enter number of tickets: ")
        if tickets is None or tickets <= 0:
            print("❌ Invalid number of tickets.")
            return

        if tickets > remaining:
            print(f"❌ Not enough seats. Available: {remaining}, requested: {tickets}.")
            return

        payment_type = input("Enter payment type (UPI/Card/Cash): ").strip()
        if not payment_type:
            print("❌ Payment type is required.")
            return

        total_price = float(event["price"]) * tickets
        booking_status = "paid"

        conn.execute("BEGIN;")
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO bookings (user_id, event_id, no_of_tickets, payment_type, total_price, status)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, event_id, tickets, payment_type, total_price, booking_status))

        cur.execute("""
            UPDATE events
               SET occupancy = occupancy + ?
             WHERE id = ?
               AND occupancy + ? <= (SELECT capacity FROM venues WHERE id = events.venue_id);
        """, (tickets, event_id, tickets))

        if cur.rowcount == 0:
            conn.rollback()
            print("❌ Booking failed: capacity reached while processing. Please try another event.")
            return

        conn.commit()

        print("\n✅ Event booked successfully!")
        print(f"Event: {event['event_name']} | Venue: {event['venue_name']} ({event['city']}, {event['pincode']})")
        print(f"Tickets: {tickets} | Payment: {payment_type} | Total: ₹{total_price:.2f}")
        print(f"Remaining seats after booking: {event_remaining_seats(conn, event_id)}")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"❌ Booking failed due to constraint: {e}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Booking failed due to an unexpected error: {e}")
    finally:
        conn.close()

def view_my_bookings(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            b.id AS booking_id,
            b.no_of_tickets,
            b.payment_type,
            b.total_price,
            b.status AS booking_status,
            e.event_name,
            e.status AS event_status,
            v.venue_name,
            v.city,
            v.pincode
        FROM bookings b
        JOIN events e   ON b.event_id = e.id
        JOIN venues v   ON e.venue_id = v.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC;
    """, (user_id,))
    rows = cur.fetchall()

    print("\nMy Bookings:")
    if not rows:
        print("You have not booked any events yet.")
    else:
        print("-" * 120)
        for r in rows:
            print(
                f"Booking #{r['booking_id']} | Event: {r['event_name']} ({r['event_status']}) | "
                f"Venue: {r['venue_name']} ({r['city']}, {r['pincode']}) | "
                f"Tickets: {r['no_of_tickets']} | Payment: {r['payment_type']} | "
                f"Total: ₹{r['total_price']:.2f} | Status: {r['booking_status']}"
            )
        print("-" * 120)
    conn.close()

def edit_profile(user_id):
    conn = get_connection()
    user = get_user(conn, user_id)
    if not user:
        print("❌ User not found.")
        conn.close()
        return

    print("\n--- Edit Profile ---")
    print(f"Name   : {user['name']}")
    print(f"Phone  : {user['phone']}")
    print(f"Email  : {user['email']}")

    new_name = input("Enter new name (leave blank to keep): ").strip()
    new_phone = input("Enter new phone (leave blank to keep): ").strip()

    final_name = new_name if new_name else user["name"]
    final_phone = new_phone if new_phone else user["phone"]

    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE users
               SET name = ?, phone = ?
             WHERE id = ?;
        """, (final_name, final_phone, user_id))
        conn.commit()
        print("✅ Profile updated successfully!")
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to update profile: {e}")
    finally:
        conn.close()

def consumer_menu(user_id):
    while True:
        print("\n=== Consumer Menu ===")
        print("1. View Events")
        print("2. Book Event")
        print("3. Edit Profile")
        print("4. View My Bookings")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice == '1':
            view_events()
        elif choice == '2':
            book_event(user_id)
        elif choice == '3':
            edit_profile(user_id)
        elif choice == '4':
            view_my_bookings(user_id)
        elif choice == '5':
            print("👋 Exiting... Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

def main():
    init_db()
    print("\n--- Login ---")
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    if not email or not password:
        print("❌ Email and password are required. Exiting.")
        return

    conn = get_connection()
    user = get_user_by_credentials(conn, email, password)
    conn.close()

    if not user:
        print("❌ Invalid credentials. Exiting.")
        return

    print(f"\nLogged in as: {user['name']} (user_id={user['id']})")
    consumer_menu(user["id"])

if __name__ == "__main__":
    main()s