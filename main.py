"""
Main Entry Point for Hospital Doctor Appointment & Patient Registry Desktop Tool.
"""

import sys
import os

from database import DatabaseManager
from seed_data import seed_database
from gui import HospitalApp


def main():
    db_path = "hospital_registry.db"
    print("Initializing Hospital Database Manager...")
    db = DatabaseManager(db_path)

    # Check if empty database, automatically populate seed data
    if not db.get_all_doctors():
        print("Empty database detected. Seeding initial Indian doctor & patient records...")
        seed_database(db, force=False)

    print("Launching Hospital Appointment Registry Desktop Application...")
    app = HospitalApp(db)
    app.mainloop()


if __name__ == "__main__":
    main()
