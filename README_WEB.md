# Hospital Appointment Registry — Mobile Web Edition

This version replaces the Tkinter screen with a responsive website interface that works in a mobile browser. It reuses the original `database.py`, `seed_data.py`, SQLite schema, patient/doctor/appointment models, time slots, and booking conflict checks.

## Features
- Dashboard counts and upcoming appointments
- Patient registration, search, and deletion
- Doctor registration and catalog
- Appointment booking, filtering, status updates, rescheduling, and deletion
- Existing SQLite database (`hospital_registry.db`)
- Mobile-friendly layout

## Run on a computer
1. Install Python 3.10 or newer.
2. Extract the project ZIP.
3. Open a terminal in the project folder.
4. Install dependencies: `python -m pip install -r requirements.txt`
5. Start the web app: `python app.py`
6. On the same computer open `http://127.0.0.1:5000` in a browser.

To open it on a phone connected to the same Wi-Fi, run `ipconfig` (Windows) or `hostname -I` (Linux) on the computer and open `http://COMPUTER-LAN-IP:5000` on the phone. Both devices must be on the same network.

## Deploy online
Use a Python-capable hosting provider. Set the start command to `gunicorn app:app` and install `gunicorn` in the host environment. Set a strong `SECRET_KEY`. For persistent records, configure a persistent disk and set `HOSPITAL_DB_PATH` to a path on that disk; ordinary temporary hosting filesystems may reset SQLite data on redeploy/restart. Do not use real patient data on a public deployment without proper access control, HTTPS, backups, and privacy/security review. This student project has no login/authentication and is not ready for real clinical use.

## Notes
- `python main.py` still starts the original desktop Tkinter version.
- `python app.py` starts the new browser version.
- The web server must remain running while you use the local browser interface.
- Sample records are inserted automatically only when the database has no doctors.
