"""
Seed Data Script for Hospital Doctor Appointment & Patient Registry.
Populates the SQLite database with authentic Indian doctor profiles (with consultation fees in ₹ Rupees),
Indian patient demographics, and realistic appointment schedules.
"""

import datetime
from database import DatabaseManager, Doctor, Patient, Appointment


def seed_database(db: DatabaseManager, force: bool = False):
    """Populates the database with sample data if empty or if force=True."""
    existing_doctors = db.get_all_doctors()
    existing_patients = db.get_all_patients()

    if existing_doctors and existing_patients and not force:
        print("Database already contains records. Skipping seed data insertion.")
        return

    print("Seeding Indian Hospital Doctor & Patient Registry data...")

    # 1. Seed Doctors with Indian Rupees (₹) consultation fees
    doctors_data = [
        Doctor(
            name="Dr. Rajesh Sharma",
            specialization="Cardiology",
            fee_inr=1200.00,
            phone="+91 98201 45892",
            email="rajesh.sharma@apollohealth.in",
            available_days="Mon-Sat"
        ),
        Doctor(
            name="Dr. Ananya Iyer",
            specialization="Pediatrics",
            fee_inr=750.00,
            phone="+91 94440 12345",
            email="ananya.iyer@fortiscare.in",
            available_days="Mon-Fri"
        ),
        Doctor(
            name="Dr. Vikramaditya Reddy",
            specialization="Orthopedics",
            fee_inr=1500.00,
            phone="+91 98480 99887",
            email="v.reddy@kims.in",
            available_days="Tue-Sun"
        ),
        Doctor(
            name="Dr. Sunita Deshmukh",
            specialization="Gynecology & Obstetrics",
            fee_inr=900.00,
            phone="+91 98220 54321",
            email="sunita.d@sahyadri.in",
            available_days="Mon-Fri"
        ),
        Doctor(
            name="Dr. Amitav Banerjee",
            specialization="General Medicine",
            fee_inr=500.00,
            phone="+91 98300 77665",
            email="a.banerjee@peerless.in",
            available_days="Mon-Sat"
        ),
        Doctor(
            name="Dr. Meera Nair",
            specialization="Dermatology",
            fee_inr=850.00,
            phone="+91 94470 33221",
            email="meera.nair@amrita.in",
            available_days="Mon-Fri"
        )
    ]

    doctor_ids = []
    for doc in doctors_data:
        doc_id = db.add_doctor(doc)
        doctor_ids.append(doc_id)

    # 2. Seed Patients with Indian demographics
    patients_data = [
        Patient(
            name="Rahul Verma",
            age=34,
            gender="Male",
            phone="+91 98111 22334",
            email="rahul.verma@gmail.com",
            blood_group="A+",
            address="Bandra West, Mumbai, Maharashtra"
        ),
        Patient(
            name="Priya Patel",
            age=28,
            gender="Female",
            phone="+91 98250 88776",
            email="priya.patel@yahoo.co.in",
            blood_group="B+",
            address="Satellite, Ahmedabad, Gujarat"
        ),
        Patient(
            name="Suresh Kumar",
            age=52,
            gender="Male",
            phone="+91 94441 55667",
            email="suresh.k@outlook.com",
            blood_group="O+",
            address="Anna Nagar, Chennai, Tamil Nadu"
        ),
        Patient(
            name="Kavita Sharma",
            age=41,
            gender="Female",
            phone="+91 98102 33445",
            email="kavita.s@gmail.com",
            blood_group="AB+",
            address="Connaught Place, New Delhi, Delhi"
        ),
        Patient(
            name="Amit Joshi",
            age=29,
            gender="Male",
            phone="+91 98231 66778",
            email="amit.j@rediffmail.com",
            blood_group="A-",
            address="Kothrud, Pune, Maharashtra"
        ),
        Patient(
            name="Deepa Gupta",
            age=65,
            gender="Female",
            phone="+91 98310 44556",
            email="deepa.gupta@gmail.com",
            blood_group="O-",
            address="Salt Lake, Kolkata, West Bengal"
        ),
        Patient(
            name="Arjun Mehta",
            age=19,
            gender="Male",
            phone="+91 98450 11223",
            email="arjun.m@indiatimes.com",
            blood_group="B-",
            address="Indiranagar, Bengaluru, Karnataka"
        ),
        Patient(
            name="Lakshmi Narayanan",
            age=48,
            gender="Female",
            phone="+91 98400 99112",
            email="lakshmi.n@gmail.com",
            blood_group="AB-",
            address="Jubilee Hills, Hyderabad, Telangana"
        )
    ]

    patient_ids = []
    for pat in patients_data:
        p_id, _ = db.add_patient(pat)
        patient_ids.append(p_id)

    # 3. Seed Appointments relative to current date
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    day_after = today + datetime.timedelta(days=2)
    yesterday = today - datetime.timedelta(days=1)

    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    day_after_str = day_after.strftime("%Y-%m-%d")
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    sample_appointments = [
        # Today's appointments
        Appointment(
            patient_id=patient_ids[0],  # Rahul Verma
            doctor_id=doctor_ids[0],   # Dr. Rajesh Sharma (Cardiology)
            appointment_date=today_str,
            time_slot="09:00 - 10:00",
            status="Completed",
            notes="Routine ECG checkup and hypertension consultation."
        ),
        Appointment(
            patient_id=patient_ids[1],  # Priya Patel
            doctor_id=doctor_ids[1],   # Dr. Ananya Iyer (Pediatrics)
            appointment_date=today_str,
            time_slot="10:00 - 11:00",
            status="Scheduled",
            notes="Vaccination and routine pediatric checkup."
        ),
        Appointment(
            patient_id=patient_ids[2],  # Suresh Kumar
            doctor_id=doctor_ids[2],   # Dr. Vikramaditya Reddy (Orthopedics)
            appointment_date=today_str,
            time_slot="11:00 - 12:00",
            status="Scheduled",
            notes="Knee joint pain consultation and X-ray review."
        ),
        Appointment(
            patient_id=patient_ids[3],  # Kavita Sharma
            doctor_id=doctor_ids[4],   # Dr. Amitav Banerjee (General Medicine)
            appointment_date=today_str,
            time_slot="14:00 - 15:00",
            status="Scheduled",
            notes="Seasonal viral fever checkup."
        ),
        # Tomorrow's appointments
        Appointment(
            patient_id=patient_ids[4],  # Amit Joshi
            doctor_id=doctor_ids[5],   # Dr. Meera Nair (Dermatology)
            appointment_date=tomorrow_str,
            time_slot="09:00 - 10:00",
            status="Scheduled",
            notes="Allergy skin patch test."
        ),
        Appointment(
            patient_id=patient_ids[5],  # Deepa Gupta
            doctor_id=doctor_ids[0],   # Dr. Rajesh Sharma (Cardiology)
            appointment_date=tomorrow_str,
            time_slot="11:00 - 12:00",
            status="Scheduled",
            notes="Follow-up consultation for blood pressure."
        ),
        Appointment(
            patient_id=patient_ids[6],  # Arjun Mehta
            doctor_id=doctor_ids[3],   # Dr. Sunita Deshmukh (Gynecology - e.g. general youth care / sports medicine referral)
            appointment_date=day_after_str,
            time_slot="15:00 - 16:00",
            status="Scheduled",
            notes="Consultation regarding fatigue & vitamin deficiency."
        ),
        # Yesterday's past appointment
        Appointment(
            patient_id=patient_ids[7],  # Lakshmi Narayanan
            doctor_id=doctor_ids[4],   # Dr. Amitav Banerjee
            appointment_date=yesterday_str,
            time_slot="16:00 - 17:00",
            status="Completed",
            notes="Diabetes blood sugar report evaluation."
        )
    ]

    for apt in sample_appointments:
        try:
            db.book_appointment(apt)
        except ValueError as e:
            print(f"Skipping seeding conflict: {e}")

    print("Database seeding completed successfully.")


if __name__ == "__main__":
    db_mgr = DatabaseManager("hospital_registry.db")
    seed_database(db_mgr, force=True)
