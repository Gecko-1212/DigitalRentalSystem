# Digital Equipment Rental System

## 📌 Overview

The **Digital Equipment Rental System** is a university-focused platform that streamlines the process of borrowing, reserving, and managing special equipment (e.g., routers, laptops, switches) required for student assignments and projects.

It supports two main user roles:
- **Students**: Can view, reserve, and return equipment.
- **Staff (Administrators)**: Can manage inventory, track overdue or damaged items, and generate usage reports.

The system is powered by **Supabase (PostgreSQL)** for database operations and **Python** for backend logic, using the `psycopg2` library to interact with the database.

---

## ✨ Key Features

- User account creation and role-based access.
- Password-protected login.
- Equipment booking, return, and availability checks.
- Admin functionality to flag items (e.g., lost, damaged).
- Reporting tools for popular equipment and overdue returns.
- Enforced date validation and availability checks to prevent double bookings.

---

## 🛠 Technologies Used

- **Python 3.10+**
- **Supabase** – PostgreSQL backend with web GUI
- **psycopg2** – PostgreSQL adapter for Python
- **dotenv** – For environment variable management
- **datetime** – For date and time processing
- **os** – File path/environment management

---

## 🧱 Database Schema (Simplified)

Key tables:
- `Student_Staff`: All users, with role differentiation
- `User_Account`: Login credentials
- `Equipment`: List of all rentable equipment
- `Reservation`: Equipment booking records


---

## 🧪 Setup Instructions

Follow these steps to get the project up and running on your machine:

### 1. Create a Supabase Account and Project

- Go to [Supabase](https://supabase.com) and **sign up** for a free account if you don’t have one.  
- After logging in, click **"New Project"** and fill in the details (project name, password, region).  
- Wait for your project to be initialized.

### 2. Get Your Database Connection Details

- In the Supabase dashboard, click on **Settings > Database**.  
- Note down the following details:
  - `user` (database user)  
  - `password` (your database password)  
  - `host` (your database host URL)  
  - `port` (usually 5432)  
  - `dbname` (database name)

### 3. Set Up Your Environment Variables

- In the project folder, create a file named `.env`.  
- Add your database connection details exactly as shown in the `.env.example` file. 

### 4. Generate and Import Test Data (Optional)

- A Python script is provided to generate sample test data for users, equipment, and reservations.  
- Run this script to produce CSV files with test entries.  
- Inmport these CSV files into the respective tables in Supabase.  
- This step helps you populate the database quickly with realistic data to test the system.

### 5. Install Python Dependencies

- Make sure you have Python 3 installed. Then, in your project directory, run:

```bash
pip install -r requirements.txt


```bash
git clone https://github.com/Gecko-1212/DigitalRentalSystem.git
cd DigitalRentalSystem
