import psycopg2
from dotenv import load_dotenv
import os
from datetime import datetime


# Database Connection
def get_db_connection_and_cursor():
    load_dotenv()
    conn = psycopg2.connect(
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
        port=os.getenv("port"),
        dbname=os.getenv("dbname")
    )
    cursor = conn.cursor()
    return conn, cursor


# Create tables 
def initialize_db(cursor, conn):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Student_Staff (
        id SERIAL PRIMARY KEY,
        fullname VARCHAR(50) NOT NULL,
        email VARCHAR(50) NOT NULL UNIQUE,
        role VARCHAR(10) CHECK (role IN ('Student', 'Staff'))
    );
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS User_Account (
        id INT PRIMARY KEY REFERENCES Student_Staff(id),
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Equipment (
        equipment_id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        equipment_condition VARCHAR(20) DEFAULT 'Good',
        equipment_availability BOOLEAN DEFAULT TRUE
    );
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Reservation (
        reservation_id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL REFERENCES User_Account(username),
        equipment_id INT NOT NULL REFERENCES Equipment(equipment_id),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(20) DEFAULT 'Active'
    );
    """)
    conn.commit()


# SQL-Queries
    cursor.execute("DROP FUNCTION IF EXISTS check_person_exists(VARCHAR, VARCHAR);")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION check_person_exists(p_email VARCHAR, p_fullname VARCHAR)
    RETURNS BOOLEAN AS $$
    DECLARE
        exists BOOLEAN;
    BEGIN
        SELECT EXISTS (SELECT 1 FROM Student_Staff WHERE email = p_email AND fullname = p_fullname) INTO exists;
        RETURN exists;
    END;
    $$ LANGUAGE plpgsql;
    """)


    cursor.execute("DROP FUNCTION IF EXISTS check_username_exists(VARCHAR);")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION check_username_exists(p_username VARCHAR)
    RETURNS BOOLEAN AS $$
    DECLARE
        exists BOOLEAN;
    BEGIN
        SELECT EXISTS (SELECT 1 FROM User_Account WHERE username = p_username) INTO exists;
        RETURN exists;
    END;
    $$ LANGUAGE plpgsql;
    """)


    cursor.execute("DROP FUNCTION IF EXISTS check_credentials(VARCHAR, VARCHAR);")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION check_credentials(p_username VARCHAR, p_password VARCHAR)
    RETURNS BOOLEAN AS $$
    DECLARE
        valid BOOLEAN;
    BEGIN
        SELECT EXISTS (
            SELECT 1 FROM User_Account WHERE username = p_username AND password = p_password) INTO valid;
            RETURN valid;
    END;
    $$ LANGUAGE plpgsql;
    """)


    cursor.execute("DROP FUNCTION IF EXISTS add_user_account(VARCHAR, VARCHAR, VARCHAR);")
    cursor.execute("""
    CREATE OR REPLACE FUNCTION add_user_account(p_email VARCHAR, p_username VARCHAR, p_password VARCHAR)
    RETURNS BOOLEAN AS $$
    DECLARE
        user_id INT;
        exists BOOLEAN;
    BEGIN
        SELECT id INTO user_id FROM Student_Staff WHERE email = p_email;
        IF user_id IS NULL THEN
            RETURN FALSE;
        END IF;

        SELECT EXISTS(SELECT 1 FROM User_Account WHERE id = user_id) INTO exists;
        IF exists THEN
            RETURN FALSE;
        ELSE
            INSERT INTO User_Account (id, username, password) VALUES (user_id, p_username, p_password);
            RETURN TRUE;
        END IF;
    END;
    $$ LANGUAGE plpgsql;
    """)


    cursor.execute("DROP PROCEDURE IF EXISTS make_reservation_proc(VARCHAR, INT, DATE, DATE);")
    cursor.execute("""
    CREATE OR REPLACE PROCEDURE make_reservation_proc(
        p_username VARCHAR,
        p_equipment_id INT,
        p_start_date DATE,
        p_end_date DATE
    )
    LANGUAGE plpgsql
    AS $$
    DECLARE
        available BOOLEAN;
        conflict_count INT;
    BEGIN
        SELECT equipment_availability INTO available FROM Equipment WHERE equipment_id = p_equipment_id;
        IF available IS NULL THEN
            RAISE EXCEPTION 'Equipment ID % does not exist.', p_equipment_id;
        END IF;

        IF NOT available THEN
            RAISE EXCEPTION 'Equipment is currently not available.';
        END IF;

        SELECT COUNT(*) INTO conflict_count FROM Reservation
        WHERE equipment_id = p_equipment_id
          AND status = 'Active'
          AND (p_start_date <= end_date AND p_end_date >= start_date);

        IF conflict_count > 0 THEN
            RAISE EXCEPTION 'Equipment is already reserved for the selected date range.';
        END IF;

        INSERT INTO Reservation (username, equipment_id, start_date, end_date, status)
        VALUES (p_username, p_equipment_id, p_start_date, p_end_date, 'Active');

        UPDATE Equipment SET equipment_availability = FALSE WHERE equipment_id = p_equipment_id;

        RAISE NOTICE 'Reservation successful.';
    END;
    $$;
    """)
    conn.commit()


# Helper Functions
def check_person_exists(cursor, fullname, email):
    cursor.execute("SELECT check_person_exists(%s, %s);", (email, fullname))
    return cursor.fetchone()[0]


def check_username_exists(cursor, username):
    cursor.execute("SELECT check_username_exists(%s);", (username,))
    return cursor.fetchone()[0]


def check_credentials(cursor, username, password):
    cursor.execute("SELECT check_credentials(%s, %s);", (username, password))
    return cursor.fetchone()[0]


def add_user_account(conn, cursor, email, username, password):
    cursor.execute("SELECT add_user_account(%s, %s, %s);", (email, username, password))
    result = cursor.fetchone()[0]
    conn.commit()
    return result


def get_user_role(cursor, email):
    cursor.execute("SELECT role FROM Student_Staff WHERE email = %s;", (email,))
    role = cursor.fetchone()
    return role[0] if role else None


def view_equipment_catalog(cursor):
    cursor.execute("SELECT equipment_id, name, equipment_condition, equipment_availability FROM Equipment;")
    return cursor.fetchall()


def check_equipment_availability(cursor, equipment_id):
    cursor.execute("SELECT equipment_availability FROM Equipment WHERE equipment_id = %s;", (equipment_id,))
    result = cursor.fetchone()
    if result is None:
        return None  
    return result[0]  


def call_make_reservation_proc(conn, cursor, username, equipment_id, start_date, end_date):
    try:
        cursor.execute("CALL make_reservation_proc(%s, %s, %s, %s);", (username, equipment_id, start_date, end_date))
        conn.commit()
        print("Reservation successful.")
    except psycopg2.Error as e:
        print(f"Reservation failed: {e.pgerror.strip()}")


def return_equipment(conn, cursor, reservation_id):
    cursor.execute("""
        SELECT equipment_id FROM Reservation WHERE reservation_id = %s AND status = 'Active';
    """, (reservation_id,))
    row = cursor.fetchone()
    if not row:
        print("No active reservation found with that ID.")
        return False
    equipment_id = row[0]
    cursor.execute("UPDATE Reservation SET status = 'Returned' WHERE reservation_id = %s;", (reservation_id,))
    cursor.execute("UPDATE Equipment SET equipment_availability = TRUE WHERE equipment_id = %s;", (equipment_id,))
    conn.commit()
    return True


def view_user_reservations(cursor, username):
    cursor.execute("""
    SELECT r.reservation_id, e.name, r.start_date, r.end_date, r.status
    FROM Reservation r
    JOIN Equipment e ON r.equipment_id = e.equipment_id
    WHERE r.username = %s
    ORDER BY r.start_date DESC;
    """, (username,))
    return cursor.fetchall()


def mark_equipment_status(conn, cursor, equipment_id, new_status):
    cursor.execute("SELECT equipment_id FROM Equipment WHERE equipment_id = %s;", (equipment_id,))
    if cursor.fetchone() is None:
        print(f"No equipment with ID {equipment_id} found.")
        return False
    if new_status not in ('Lost', 'Damaged', 'Worn Out', 'Poor', 'Good' ):
        print("Invalid status.")
        return False
    cursor.execute("UPDATE Equipment SET equipment_condition = %s, equipment_availability = FALSE WHERE equipment_id = %s;", (new_status, equipment_id))
    conn.commit()
    print(f"Equipment {equipment_id} marked as {new_status}.")
    return True


def mark_reservation_overdue(conn, cursor, reservation_id):
    cursor.execute("""
        SELECT equipment_id, end_date, status
        FROM Reservation
        WHERE reservation_id = %s;
    """, (reservation_id,))
    result = cursor.fetchone()
    if not result:
        print("Reservation not found.")
        return False
    equipment_id, end_date, status = result
    if status not in ('Active', 'Ongoing2'):
        print("Only active reservations can be marked as overdue.")
        return False
    if datetime.now().date() <= end_date:
        print("The reservation is not overdue yet.")
        return False
    cursor.execute("""
        UPDATE Reservation SET status = 'Overdue' WHERE reservation_id = %s;
    """, (reservation_id,))
    cursor.execute("""
        UPDATE Equipment SET equipment_availability = FALSE WHERE equipment_id = %s;
    """, (equipment_id,))
    conn.commit()
    print(f"Reservation {reservation_id} marked as overdue.")
    return True


def get_top_borrowed_equipment(cursor):
    cursor.execute("""
    SELECT e.name, COUNT(r.reservation_id) AS borrow_count
    FROM Equipment e
    JOIN Reservation r ON e.equipment_id = r.equipment_id
    GROUP BY e.name
    ORDER BY borrow_count DESC
    LIMIT 3;
    """)
    return cursor.fetchall()


def view_overdue_reservations(cursor):
    cursor.execute("""
    SELECT r.reservation_id, r.username, e.name, r.start_date, r.end_date, r.status
    FROM Reservation r
    JOIN Equipment e ON r.equipment_id = e.equipment_id
    WHERE r.status = 'Overdue'
    ORDER BY r.end_date ASC;
    """)
    return cursor.fetchall()


#Login information
def input_account_info():
    full_name = input("\nEnter full name: ")
    email = input("Enter email: ")
    username = input("Choose a username: ")
    password = input("Choose a password: ")
    return full_name, email, username, password


def input_login():
    username = input("Enter username: ")
    password = input("Enter password: ")
    return username, password


def validate_date_format(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


#Menu & main functions
def student_menu(conn, cursor, username):
    while True:
        conn.rollback()
        print("""
Student Menu:
1. View equipment catalog
2. View equipment availability
3. Make a reservation
4. Return equipment
5. View my reservations
0. Logout
        """)
        choice = input("Choose an option: ")
        if choice == '1':
            try:
                catalog = view_equipment_catalog(cursor)
                for eq in catalog:
                    print(f"ID: {eq[0]}, Name: {eq[1]}, Condition: {eq[2]}, Available: {'Yes' if eq[3] else 'No'}")
            except Exception as e:
                conn.rollback()
                print(f"Error fetching catalog: {e}")
        elif choice == '2':
            try:
                equipment_id = int(input("Enter equipment ID to check availability: "))
                available = check_equipment_availability(cursor, equipment_id)
                if available is None:
                    print("There is no equipment with this ID.")
                elif available:
                    print("Available!")
                else:
                    print("Currently unavailable.")
            except ValueError:
                print("Invalid equipment ID. Please enter a number.")
            except Exception as e:
                conn.rollback()
                print(f"Error checking availability: {e}")
        elif choice == '3':
            try:
                equipment_id = int(input("Enter equipment ID to reserve: "))
                start_date_str = input("Enter start date (YYYY-MM-DD): ")
                end_date_str = input("Enter end date (YYYY-MM-DD): ")
                start_date = validate_date_format(start_date_str)
                end_date = validate_date_format(end_date_str)
                if not start_date or not end_date:
                    print("Invalid date format. Please use YYYY-MM-DD.")
                    continue
                if start_date > end_date:
                    print("Start date cannot be after end date.")
                    continue
                call_make_reservation_proc(conn, cursor, username, equipment_id, start_date, end_date)
            except ValueError:
                print("Invalid input. Please enter numeric values where required.")
            except Exception as e:
                conn.rollback()
                print(f"Reservation failed: {e}")
        elif choice == '4':
            try:
                reservation_id = int(input("Enter reservation ID to return: "))
                success = return_equipment(conn, cursor, reservation_id)
                if success:
                    print("Equipment returned successfully!")
            except ValueError:
                print("Invalid reservation ID. Please enter a number.")
            except Exception as e:
                conn.rollback()
                print(f"Return failed: {e}")
        elif choice == '5':
            try:
                reservations = view_user_reservations(cursor, username)
                for r in reservations:
                    print(f"Reservation ID: {r[0]}, Equipment: {r[1]}, From: {r[2]}, To: {r[3]}, Status: {r[4]}")
            except Exception as e:
                conn.rollback()
                print(f"Failed to fetch reservations: {e}")
        elif choice == '0':
            break
        else:
            print("Invalid option.")


def staff_menu(conn, cursor, username):
    conn.rollback()
    while True:
        print("""
Staff Menu:
1. View equipment catalog
2. View overdue reservations
3. Mark equipment condition as Lost, Damaged, Poor or Good
4. View top 3 most borrowed equipment
5. Mark reservation as overdue
0. Logout
        """)
        choice = input("Choose an option: ")
        if choice == '1':
            try:
                catalog = view_equipment_catalog(cursor)
                for eq in catalog:
                    print(f"ID: {eq[0]}, Name: {eq[1]}, Condition: {eq[2]}, Available: {'Yes' if eq[3] else 'No'}")
            except Exception as e:
                conn.rollback()
                print(f"Error fetching catalog: {e}")
        elif choice == '2':
            try:
                overdue = view_overdue_reservations(cursor)
                for o in overdue:
                    print(f"Reservation ID: {o[0]}, User: {o[1]}, Equipment: {o[2]}, From: {o[3]}, To: {o[4]}, Status: {o[5]}")
            except Exception as e:
                conn.rollback()
                print(f"Error fetching overdue reservations: {e}")
        elif choice == '3':
            try:
                equipment_id = int(input("Enter equipment ID to update status: "))
                new_status = input("Enter new status (Returned, Lost, Damaged, Worn Out, Poor, Good): ")
                mark_equipment_status(conn, cursor, equipment_id, new_status)
            except ValueError:
                print("Invalid equipment ID.")
            except Exception as e:
                conn.rollback()
                print(f"Error updating equipment status: {e}")
        elif choice == '4':
            try:
                top_equipment = get_top_borrowed_equipment(cursor)
                for i, e in enumerate(top_equipment, 1):
                    print(f"{i}. {e[0]} (Borrowed {e[1]} times)")
            except Exception as e:
                conn.rollback()
                print(f"Error fetching top equipment: {e}")
        elif choice == '5':
            try:
                reservation_id = int(input("Enter reservation ID to mark as overdue: "))
                mark_reservation_overdue(conn, cursor, reservation_id)
            except ValueError:
                print("Invalid reservation ID.")
            except Exception as e:
                conn.rollback()
                print(f"Error marking overdue: {e}")
        elif choice == '0':
            break
        else:
            print("Invalid option.")


def main():
    conn, cursor = get_db_connection_and_cursor()
    initialize_db(cursor, conn)

    print("Welcome to Equipment Reservation System!")

    while True:
        print("""
Main Menu:
1. Register
2. Login
0. Exit
        """)
        choice = input("Choose an option: ")
        if choice == '1':
            full_name, email, username, password = input_account_info()
            if not check_person_exists(cursor, full_name, email):
                print("No record found. You must be a registered student or staff first.")
                continue
            if check_username_exists(cursor, username):
                print("Username already exists.")
                continue
            success = add_user_account(conn, cursor, email, username, password)
            print("Registration successful! You can now log in." if success else "Registration failed or account already exists.")
        elif choice == '2':
            username, password = input_login()
            if check_credentials(cursor, username, password):
                cursor.execute("SELECT ss.role FROM User_Account ua JOIN Student_Staff ss ON ua.id = ss.id WHERE ua.username = %s;", (username,))
                role = cursor.fetchone()[0]
                if role == 'Student':
                    student_menu(conn, cursor, username)
                else:
                    staff_menu(conn, cursor, username)
            else:
                print("Invalid username or password.")
        elif choice == '0':
            print("Exiting program...")
            break
        else:
            print("Invalid option.")

            
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()