"""Mobile-friendly Flask interface for the Hospital Appointment Registry."""
import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
from database import DatabaseManager, Doctor, Patient, Appointment
from seed_data import seed_database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('HOSPITAL_DB_PATH', os.path.join(BASE_DIR, 'hospital_registry.db'))
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-before-public-deployment')
db = DatabaseManager(DB_PATH)
if not db.get_all_doctors():
    seed_database(db, force=False)

@app.context_processor
def inject_globals():
    return {'today': date.today().isoformat(), 'slots': db.TIME_SLOTS, 'blood_groups': db.BLOOD_GROUPS}

@app.route('/')
def dashboard():
    stats = db.get_dashboard_stats()
    upcoming = sorted([a for a in db.get_all_appointments() if a.appointment_date >= date.today().isoformat() and a.status != 'Cancelled'], key=lambda a: (a.appointment_date, a.time_slot))[:8]
    return render_template('dashboard.html', stats=stats, upcoming=upcoming)

@app.route('/patients', methods=['GET', 'POST'])
def patients():
    if request.method == 'POST':
        f = request.form
        try:
            age = int(f.get('age', ''))
            if age < 0 or age > 120: raise ValueError('Enter a valid age (0–120).')
            phone = f.get('phone','').strip()
            if not phone.replace('+','').replace('-','').replace(' ','').replace('(','').replace(')','').isdigit() or len(phone) < 8:
                raise ValueError('Enter a valid phone number.')
            p = Patient(name=f['name'].strip(), age=age, gender=f['gender'], phone=phone, email=f.get('email','').strip(), blood_group=f.get('blood_group',''), address=f.get('address','').strip())
            _, code = db.add_patient(p)
            flash(f'Patient registered successfully. Patient ID: {code}', 'success')
        except Exception as e: flash(str(e) or 'Could not register patient.', 'error')
        return redirect(url_for('patients'))
    q = request.args.get('q','').strip()
    records = db.search_patients(q) if q else db.get_all_patients()
    return render_template('patients.html', patients=records, q=q)

@app.post('/patients/<int:pid>/delete')
def delete_patient(pid):
    try: db.delete_patient(pid); flash('Patient deleted.', 'success')
    except Exception as e: flash(f'Unable to delete patient: {e}', 'error')
    return redirect(url_for('patients'))

@app.route('/doctors', methods=['GET','POST'])
def doctors():
    if request.method == 'POST':
        f=request.form
        try:
            fee=float(f['fee_inr'])
            if fee < 0: raise ValueError('Fee cannot be negative.')
            db.add_doctor(Doctor(name=f['name'].strip(), specialization=f['specialization'].strip(), fee_inr=fee, phone=f['phone'].strip(), email=f.get('email','').strip(), available_days=f.get('available_days','Mon-Fri').strip()))
            flash('Doctor added successfully.', 'success')
        except Exception as e: flash(str(e) or 'Could not add doctor.', 'error')
        return redirect(url_for('doctors'))
    return render_template('doctors.html', doctors=db.get_all_doctors())

@app.post('/doctors/<int:did>/delete')
def delete_doctor(did):
    try: db.delete_doctor(did); flash('Doctor deleted.', 'success')
    except Exception as e: flash(f'Unable to delete doctor: {e}', 'error')
    return redirect(url_for('doctors'))

@app.route('/appointments', methods=['GET','POST'])
def appointments():
    if request.method == 'POST':
        f=request.form
        try:
            date.fromisoformat(f['appointment_date'])
            apt=Appointment(patient_id=int(f['patient_id']), doctor_id=int(f['doctor_id']), appointment_date=f['appointment_date'], time_slot=f['time_slot'], status='Scheduled', notes=f.get('notes','').strip())
            _, code=db.book_appointment(apt)
            flash(f'Appointment booked. Reference: {code}', 'success')
        except Exception as e: flash(str(e) or 'Could not book appointment.', 'error')
        return redirect(url_for('appointments'))
    doctor_filter=request.args.get('doctor_id', type=int)
    status=request.args.get('status','All')
    q=request.args.get('q','').strip()
    records=db.get_appointments_filtered(doctor_id=doctor_filter, status=status, search_query=q)
    return render_template('appointments.html', appointments=records, doctors=db.get_all_doctors(), patients=db.get_all_patients(), doctor_filter=doctor_filter, status=status, q=q)

@app.post('/appointments/<int:aid>/status')
def appointment_status(aid):
    try: db.update_appointment_status(aid, request.form['status']); flash('Appointment status updated.', 'success')
    except Exception as e: flash(str(e), 'error')
    return redirect(url_for('appointments'))

@app.post('/appointments/<int:aid>/reschedule')
def reschedule(aid):
    try:
        date.fromisoformat(request.form['appointment_date'])
        db.reschedule_appointment(aid, request.form['appointment_date'], request.form['time_slot'])
        flash('Appointment rescheduled.', 'success')
    except Exception as e: flash(str(e), 'error')
    return redirect(url_for('appointments'))

@app.post('/appointments/<int:aid>/delete')
def delete_appointment(aid):
    try: db.delete_appointment(aid); flash('Appointment deleted.', 'success')
    except Exception as e: flash(str(e), 'error')
    return redirect(url_for('appointments'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
