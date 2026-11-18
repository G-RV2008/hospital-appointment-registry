"""
Database Access Layer & OOP Data Models for Hospital Doctor Appointment & Patient Registry.
Uses SQLite3 with SQL-based double-booking prevention.
"""

import sqlite3
import os
import datetime
from typing import List, Optional, Tuple, Dict, Any


class Doctor:
    """Represents a Medical Doctor in the hospital registry."""
    def __init__(
        self,
        name: str,
        specialization: str,
        fee_inr: float,
        phone: str,
        email: str,
        available_days: str = "Mon-Fri",
        doctor_id: Optional[int] = None
    ):
        self.id = doctor_id
        self.name = name
        self.specialization = specialization
        self.fee_inr = fee_inr
        self.phone = phone
        self.email = email
        self.available_days = available_days

    @property
    def fee_formatted(self) -> str:
        """Return formatted fee in Indian Rupees (₹)."""
        return f"₹ {self.fee_inr:,.2f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "specialization": self.specialization,
            "fee_inr": self.fee_inr,
            "fee_formatted": self.fee_formatted,
            "phone": self.phone,
            "email": self.email,
            "available_days": self.available_days
        }


class Patient:
    """Represents a Patient in the registry."""
    def __init__(
        self,
        name: str,
        age: int,
        gender: str,
        phone: str,
        email: str,
        blood_group: str,
        address: str,
        patient_code: Optional[str] = None,
        patient_id: Optional[int] = None
    ):
        self.id = patient_id
        self.patient_code = patient_code
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.email = email
        self.blood_group = blood_group
        self.address = address

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "patient_code": self.patient_code,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "phone": self.phone,
            "email": self.email,
            "blood_group": self.blood_group,
            "address": self.address
        }


class Appointment:
    """Represents a Doctor Appointment."""
    def __init__(
        self,
        patient_id: int,
        doctor_id: int,
        appointment_date: str,  # YYYY-MM-DD
        time_slot: str,         # e.g., "09:00 - 10:00"
        status: str = "Scheduled", # Scheduled, Completed, Cancelled
        notes: str = "",
        appointment_code: Optional[str] = None,
        appointment_id: Optional[int] = None,
        created_at: Optional[str] = None,
        patient_name: Optional[str] = None,
        doctor_name: Optional[str] = None,
        specialization: Optional[str] = None,
        fee_inr: Optional[float] = None
    ):
        self.id = appointment_id
        self.appointment_code = appointment_code
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_date = appointment_date
        self.time_slot = time_slot
        self.status = status
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Joined fields for UI convenience
        self.patient_name = patient_name or ""
        self.doctor_name = doctor_name or ""
        self.specialization = specialization or ""
        self.fee_inr = fee_inr or 0.0

    @property
    def fee_formatted(self) -> str:
        return f"₹ {self.fee_inr:,.2f}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "appointment_code": self.appointment_code,
            "patient_id": self.patient_id,
            "patient_name": self.patient_name,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor_name,
            "specialization": self.specialization,
            "appointment_date": self.appointment_date,
            "time_slot": self.time_slot,
            "status": self.status,
            "notes": self.notes,
            "fee_inr": self.fee_inr,
            "fee_formatted": self.fee_formatted,
            "created_at": self.created_at
        }


class DatabaseManager:
    """Manages SQLite database connections, schema creation, CRUD operations, and double-booking SQL queries."""
    
    TIME_SLOTS = [
        "09:00 - 10:00",
        "10:00 - 11:00",
        "11:00 - 12:00",
        "12:00 - 13:00",
        "14:00 - 15:00",
        "15:00 - 16:00",
        "16:00 - 17:00",
        "17:00 - 18:00"
    ]

    BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

    def __init__(self, db_path: str = "hospital_registry.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Initialize database schema with tables and indexes."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Doctors Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                fee_inr REAL NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                available_days TEXT DEFAULT 'Mon-Fri'
            );
            """)

            # Patients Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                blood_group TEXT,
                address TEXT
            );
            """)

            # Appointments Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_code TEXT UNIQUE NOT NULL,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
            );
            """)

            # Index for high-performance double-booking validation SQL queries
            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_doctor_slot 
            ON appointments(doctor_id, appointment_date, time_slot, status);
            """)

            conn.commit()
        finally:
            conn.close()

    # ==================== DOUBLE-BOOKING SQL CHECKS ====================

    def is_doctor_booked(self, doctor_id: int, appointment_date: str, time_slot: str, exclude_appointment_id: Optional[int] = None) -> bool:
        """
        Executes SQL query to check if doctor is already booked for the given date & hourly slot.
        Ignores 'Cancelled' appointments.
        Returns True if doctor IS booked (conflict), False if available.
        """
        query = """
        SELECT COUNT(*) as conflict_count 
        FROM appointments 
        WHERE doctor_id = ? 
          AND appointment_date = ? 
          AND time_slot = ? 
          AND status != 'Cancelled'
        """
        params = [doctor_id, appointment_date, time_slot]

        if exclude_appointment_id:
            query += " AND id != ?"
            params.append(exclude_appointment_id)

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row["conflict_count"] > 0
        finally:
            conn.close()

    def is_patient_booked(self, patient_id: int, appointment_date: str, time_slot: str, exclude_appointment_id: Optional[int] = None) -> bool:
        """
        Executes SQL query to check if patient already has another active appointment at the same slot.
        Returns True if patient IS booked elsewhere (conflict), False if available.
        """
        query = """
        SELECT COUNT(*) as conflict_count 
        FROM appointments 
        WHERE patient_id = ? 
          AND appointment_date = ? 
          AND time_slot = ? 
          AND status != 'Cancelled'
        """
        params = [patient_id, appointment_date, time_slot]

        if exclude_appointment_id:
            query += " AND id != ?"
            params.append(exclude_appointment_id)

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return row["conflict_count"] > 0
        finally:
            conn.close()

    # ==================== DOCTOR CRUD ====================

    def add_doctor(self, doctor: Doctor) -> int:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO doctors (name, specialization, fee_inr, phone, email, available_days)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (doctor.name, doctor.specialization, doctor.fee_inr, doctor.phone, doctor.email, doctor.available_days))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_doctor(self, doctor: Doctor) -> bool:
        if not doctor.id:
            return False
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE doctors
            SET name = ?, specialization = ?, fee_inr = ?, phone = ?, email = ?, available_days = ?
            WHERE id = ?;
            """, (doctor.name, doctor.specialization, doctor.fee_inr, doctor.phone, doctor.email, doctor.available_days, doctor.id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_doctor(self, doctor_id: int) -> bool:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doctors WHERE id = ?;", (doctor_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_all_doctors(self) -> List[Doctor]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [
                Doctor(
                    doctor_id=r["id"],
                    name=r["name"],
                    specialization=r["specialization"],
                    fee_inr=r["fee_inr"],
                    phone=r["phone"],
                    email=r["email"],
                    available_days=r["available_days"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM doctors WHERE id = ?;", (doctor_id,))
            r = cursor.fetchone()
            if r:
                return Doctor(
                    doctor_id=r["id"],
                    name=r["name"],
                    specialization=r["specialization"],
                    fee_inr=r["fee_inr"],
                    phone=r["phone"],
                    email=r["email"],
                    available_days=r["available_days"]
                )
            return None
        finally:
            conn.close()

    # ==================== PATIENT CRUD ====================

    def generate_patient_code(self) -> str:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM patients;")
            row = cursor.fetchone()
            next_id = (row["max_id"] or 0) + 1
            return f"PAT-{next_id:04d}"
        finally:
            conn.close()

    def add_patient(self, patient: Patient) -> Tuple[int, str]:
        code = patient.patient_code or self.generate_patient_code()
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO patients (patient_code, name, age, gender, phone, email, blood_group, address)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (code, patient.name, patient.age, patient.gender, patient.phone, patient.email, patient.blood_group, patient.address))
            conn.commit()
            return cursor.lastrowid, code
        finally:
            conn.close()

    def update_patient(self, patient: Patient) -> bool:
        if not patient.id:
            return False
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE patients
            SET name = ?, age = ?, gender = ?, phone = ?, email = ?, blood_group = ?, address = ?
            WHERE id = ?;
            """, (patient.name, patient.age, patient.gender, patient.phone, patient.email, patient.blood_group, patient.address, patient.id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_patient(self, patient_id: int) -> bool:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patients WHERE id = ?;", (patient_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_all_patients(self) -> List[Patient]:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [
                Patient(
                    patient_id=r["id"],
                    patient_code=r["patient_code"],
                    name=r["name"],
                    age=r["age"],
                    gender=r["gender"],
                    phone=r["phone"],
                    email=r["email"],
                    blood_group=r["blood_group"],
                    address=r["address"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    def search_patients(self, query_str: str) -> List[Patient]:
        term = f"%{query_str.strip()}%"
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM patients 
            WHERE name LIKE ? OR patient_code LIKE ? OR phone LIKE ? OR blood_group LIKE ?
            ORDER BY name ASC;
            """, (term, term, term, term))
            rows = cursor.fetchall()
            return [
                Patient(
                    patient_id=r["id"],
                    patient_code=r["patient_code"],
                    name=r["name"],
                    age=r["age"],
                    gender=r["gender"],
                    phone=r["phone"],
                    email=r["email"],
                    blood_group=r["blood_group"],
                    address=r["address"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    # ==================== APPOINTMENT BOOKING & OPERATIONS ====================

    def generate_appointment_code(self) -> str:
        today_str = datetime.date.today().strftime("%Y%m%d")
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) as max_id FROM appointments;")
            row = cursor.fetchone()
            next_id = (row["max_id"] or 0) + 1
            return f"APT-{today_str}-{next_id:03d}"
        finally:
            conn.close()

    def book_appointment(self, appointment: Appointment) -> Tuple[int, str]:
        """
        Books an appointment after verifying double-booking SQL constraints.
        Raises ValueError if doctor or patient is already booked.
        """
        if self.is_doctor_booked(appointment.doctor_id, appointment.appointment_date, appointment.time_slot):
            raise ValueError(
                f"Double-Booking Conflict! The selected doctor is already booked on {appointment.appointment_date} at {appointment.time_slot}."
            )

        if self.is_patient_booked(appointment.patient_id, appointment.appointment_date, appointment.time_slot):
            raise ValueError(
                f"Patient Conflict! Patient already has an appointment booked at {appointment.time_slot} on {appointment.appointment_date}."
            )

        code = appointment.appointment_code or self.generate_appointment_code()
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO appointments 
            (appointment_code, patient_id, doctor_id, appointment_date, time_slot, status, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                code,
                appointment.patient_id,
                appointment.doctor_id,
                appointment.appointment_date,
                appointment.time_slot,
                appointment.status or "Scheduled",
                appointment.notes or "",
                created_at
            ))
            conn.commit()
            return cursor.lastrowid, code
        finally:
            conn.close()

    def update_appointment_status(self, appointment_id: int, new_status: str) -> bool:
        if new_status not in ["Scheduled", "Completed", "Cancelled"]:
            raise ValueError("Invalid status value.")
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE appointments SET status = ? WHERE id = ?;
            """, (new_status, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def reschedule_appointment(self, appointment_id: int, new_date: str, new_slot: str) -> bool:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT doctor_id, patient_id FROM appointments WHERE id = ?;", (appointment_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError("Appointment not found.")
            
            doctor_id = row["doctor_id"]
            patient_id = row["patient_id"]

            if self.is_doctor_booked(doctor_id, new_date, new_slot, exclude_appointment_id=appointment_id):
                raise ValueError(f"Doctor is not available on {new_date} at {new_slot}.")

            if self.is_patient_booked(patient_id, new_date, new_slot, exclude_appointment_id=appointment_id):
                raise ValueError(f"Patient has another conflicting appointment at {new_slot}.")

            cursor.execute("""
            UPDATE appointments 
            SET appointment_date = ?, time_slot = ? 
            WHERE id = ?;
            """, (new_date, new_slot, appointment_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_appointment(self, appointment_id: int) -> bool:
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE id = ?;", (appointment_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_all_appointments(self) -> List[Appointment]:
        query = """
        SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization, d.fee_inr
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        ORDER BY a.appointment_date DESC, a.time_slot ASC;
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                Appointment(
                    appointment_id=r["id"],
                    appointment_code=r["appointment_code"],
                    patient_id=r["patient_id"],
                    doctor_id=r["doctor_id"],
                    appointment_date=r["appointment_date"],
                    time_slot=r["time_slot"],
                    status=r["status"],
                    notes=r["notes"],
                    created_at=r["created_at"],
                    patient_name=r["patient_name"],
                    doctor_name=r["doctor_name"],
                    specialization=r["specialization"],
                    fee_inr=r["fee_inr"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_appointments_filtered(
        self,
        doctor_id: Optional[int] = None,
        date_str: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Appointment]:
        query = """
        SELECT a.*, p.name as patient_name, d.name as doctor_name, d.specialization, d.fee_inr
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE 1=1
        """
        params: List[Any] = []

        if doctor_id:
            query += " AND a.doctor_id = ?"
            params.append(doctor_id)

        if date_str and date_str.strip():
            query += " AND a.appointment_date = ?"
            params.append(date_str.strip())

        if status and status != "All":
            query += " AND a.status = ?"
            params.append(status)

        if search_query and search_query.strip():
            term = f"%{search_query.strip()}%"
            query += " AND (p.name LIKE ? OR p.patient_code LIKE ? OR a.appointment_code LIKE ? OR d.name LIKE ?)"
            params.extend([term, term, term, term])

        query += " ORDER BY a.appointment_date DESC, a.time_slot ASC;"

        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                Appointment(
                    appointment_id=r["id"],
                    appointment_code=r["appointment_code"],
                    patient_id=r["patient_id"],
                    doctor_id=r["doctor_id"],
                    appointment_date=r["appointment_date"],
                    time_slot=r["time_slot"],
                    status=r["status"],
                    notes=r["notes"],
                    created_at=r["created_at"],
                    patient_name=r["patient_name"],
                    doctor_name=r["doctor_name"],
                    specialization=r["specialization"],
                    fee_inr=r["fee_inr"]
                )
                for r in rows
            ]
        finally:
            conn.close()

    # ==================== ANALYTICS & DASHBOARD ====================

    def get_dashboard_stats(self) -> Dict[str, Any]:
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as total FROM patients;")
            total_patients = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM doctors;")
            total_doctors = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as total FROM appointments WHERE appointment_date = ?;", (today,))
            today_appointments = cursor.fetchone()["total"]

            cursor.execute("""
            SELECT SUM(d.fee_inr) as total_rev 
            FROM appointments a 
            JOIN doctors d ON a.doctor_id = d.id 
            WHERE a.status IN ('Scheduled', 'Completed');
            """)
            total_revenue = cursor.fetchone()["total_rev"] or 0.0

            cursor.execute("SELECT status, COUNT(*) as count FROM appointments GROUP BY status;")
            status_counts = {r["status"]: r["count"] for r in cursor.fetchall()}

            return {
                "total_patients": total_patients,
                "total_doctors": total_doctors,
                "today_appointments": today_appointments,
                "total_revenue_inr": total_revenue,
                "revenue_formatted": f"₹ {total_revenue:,.2f}",
                "status_counts": status_counts
            }
        finally:
            conn.close()
