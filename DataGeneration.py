import csv
import random
from faker import Faker
from datetime import timedelta

fake = Faker()

# Define equipment names
equipment_names = [
    "Laptop", "Projector", "Camera", "Microphone", "Tablet", "Monitor",
    "Speaker", "VR Headset", "Hard Drive", "HDMI Cable", "Mouse",
    "Keyboard", "Smartphone", "3D Printer", "Laser Pointer", "Charging Station",
    "Router"
]

# --- 1. Generate Student_Staff ---
roles = ["Student", "Staff"]
student_staff = []

for i in range(1, 51):
    fullname = fake.name()
    email = f"user{i}@example.com"
    role = random.choice(roles)
    student_staff.append([i, fullname, email, role])  

with open("student_staff.csv", "w", newline="", encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "fullname", "email", "role"])
    writer.writerows(student_staff)


# --- 2. Generate User_Account ---
user_accounts = []
used_ids = random.sample(range(1, 51), 20)

for i in used_ids:
    username = f"user_{i}"
    password = fake.password(length=10)
    user_accounts.append([i, username, password])  

with open("user_account.csv", "w", newline="", encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["id", "username", "password"])
    writer.writerows(user_accounts)


# --- 3. Generate Equipment ---
equipment = []

for i in range(1, 71):
    name = random.choice(equipment_names)
    condition = random.choice(["Good",  "Worn Out", "Poor"])
    available = random.choice([True, False])
    equipment.append([i, name, condition, available])  

with open("equipment.csv", "w", newline="", encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["equipment_id", "name", "equipment_condition", "equipment_availability"])
    writer.writerows(equipment)


# --- 4. Generate Reservations ---
reservations = []
usernames = [u[1] for u in user_accounts]  

for i in range(1, 16):
    username = random.choice(usernames)
    equipment_id = random.randint(1, 70)
    start = fake.date_between(start_date="-30d", end_date="today")
    end = start + timedelta(days=random.randint(1, 10))
    status = random.choice(["Ongoing", "Returned", "Overdue"])
    reservations.append([i, username, equipment_id, start, end, status])

with open("reservations.csv", "w", newline="", encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["reservation_id", "username", "equipment_id", "start_date", "end_date", "status"])
    writer.writerows(reservations)

