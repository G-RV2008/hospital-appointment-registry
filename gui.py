"""
Tkinter Desktop Graphical User Interface for Hospital Doctor Appointment & Patient Registry.
Features modular tabs, entry forms, Treeview tables, Indian Rupee formatting (₹),
strict type validation (phone numbers, ages, fees, dates, emails),
and SQL-based double-booking prevention with tkinter.messagebox alerts.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import re
from typing import Optional

from database import DatabaseManager, Doctor, Patient, Appointment
from seed_data import seed_database


# Helper Validation Functions
def is_valid_phone(phone: str) -> bool:
    """Check if phone string contains only digits (allowing optional leading + and spaces/dashes)."""
    cleaned = phone.replace("+", "").replace("-", "").replace(" ", "").strip()
    return cleaned.isdigit() and (8 <= len(cleaned) <= 15)


def is_valid_email(email: str) -> bool:
    """Validate email format if provided."""
    if not email or not email.strip():
        return True  # Optional field
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def is_valid_name(name: str) -> bool:
    """Validate name to ensure it contains only letters, spaces, dots, and hyphens (no numbers or symbols)."""
    pattern = r"^[A-Za-z\s\.\-']+$"
    return bool(re.match(pattern, name.strip()))


def is_valid_date(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD and calendar validity."""
    try:
        datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


class HospitalApp(tk.Tk):
    """Main Application Window for Hospital Registry & Appointment Scheduler."""

    # Color Palette (Teal / Medical Theme)
    BG_MAIN = "#f8fafc"
    HEADER_BG = "#0f766e"
    HEADER_FG = "#ffffff"
    ACCENT_TEAL = "#0d9488"
    CARD_BG = "#ffffff"
    CARD_BORDER = "#cbd5e1"
    TEXT_MAIN = "#1e293b"
    TEXT_MUTED = "#64748b"

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        self.title("St. Jude Hospital - Doctor Appointment & Patient Registry")
        self.geometry("1200x760")
        self.minsize(1050, 680)
        self.configure(bg=self.BG_MAIN)

        # Selected items for editing
        self.selected_patient_id: Optional[int] = None
        self.selected_doctor_id: Optional[int] = None
        self.selected_appointment_id: Optional[int] = None

        # Register Tkinter Entry Real-Time Key Validators
        self.vcmd_digits = (self.register(self._val_digits_only), '%P')
        self.vcmd_phone = (self.register(self._val_phone_chars), '%P')
        self.vcmd_decimal = (self.register(self._val_decimal_only), '%P')
        self.vcmd_name = (self.register(self._val_name_chars), '%P')

        self._setup_styles()
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

        self._refresh_all_data()
        self._update_clock()

    # Real-Time Key Validation Handlers
    def _val_digits_only(self, P: str) -> bool:
        """Allow only numeric digits."""
        return P == "" or P.isdigit()

    def _val_phone_chars(self, P: str) -> bool:
        """Allow digits, leading +, spaces, and dashes for phone fields."""
        if P == "":
            return True
        return all(char in "0123456789+ -()" for char in P)

    def _val_decimal_only(self, P: str) -> bool:
        """Allow positive floating-point decimal numbers."""
        if P == "":
            return True
        try:
            val = float(P)
            return val >= 0
        except ValueError:
            return P.count(".") == 1 and P.replace(".", "").isdigit()

    def _val_name_chars(self, P: str) -> bool:
        """Allow letters, spaces, dots, and hyphens."""
        if P == "":
            return True
        return all(char.isalpha() or char in " .-'" for char in P)

    def _setup_styles(self):
        """Configure ttk styles for clean modern widgets."""
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        # General Notebook / Tabs
        self.style.configure("TNotebook", background=self.BG_MAIN, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=[16, 8],
            background="#e2e8f0",
            foreground=self.TEXT_MAIN,
            borderwidth=1
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", self.ACCENT_TEAL)],
            foreground=[("selected", "#ffffff")]
        )

        # Buttons
        self.style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.ACCENT_TEAL,
            foreground="#ffffff",
            borderwidth=0,
            padding=8
        )
        self.style.map("Accent.TButton", background=[("active", "#0f766e")])

        self.style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 9),
            background="#e2e8f0",
            foreground=self.TEXT_MAIN,
            padding=6
        )

        self.style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#e11d48",
            foreground="#ffffff",
            padding=6
        )

        # Treeview styling
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=26,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground=self.TEXT_MAIN
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#0f766e",
            foreground="#ffffff"
        )
        self.style.map("Treeview", background=[("selected", "#ccfbf1")], foreground=[("selected", "#0f766e")])

    def _build_header(self):
        """Build top hospital branding header bar."""
        header = tk.Frame(self, bg=self.HEADER_BG, height=65)
        header.pack(fill="x", side="top")

        title_lbl = tk.Label(
            header,
            text="🏥 St. Jude Super Speciality Hospital",
            font=("Segoe UI", 16, "bold"),
            bg=self.HEADER_BG,
            fg=self.HEADER_FG
        )
        title_lbl.pack(side="left", padx=20, pady=10)

        subtitle_lbl = tk.Label(
            header,
            text="Doctor Appointment Scheduler & Patient Registry (INR ₹)",
            font=("Segoe UI", 10, "italic"),
            bg=self.HEADER_BG,
            fg="#99f6e4"
        )
        subtitle_lbl.pack(side="left", pady=14)

        self.clock_lbl = tk.Label(
            header,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.HEADER_BG,
            fg=self.HEADER_FG
        )
        self.clock_lbl.pack(side="right", padx=20)

    def _update_clock(self):
        now_str = datetime.datetime.now().strftime("%A, %b %d, %Y  %I:%M:%S %p")
        self.clock_lbl.config(text=now_str)
        self.after(1000, self._update_clock)

    def _build_notebook(self):
        """Build tabbed main navigation."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Tab Frames
        self.tab_dashboard = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_patients = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_doctors = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_booking = tk.Frame(self.notebook, bg=self.BG_MAIN)
        self.tab_appointments = tk.Frame(self.notebook, bg=self.BG_MAIN)

        self.notebook.add(self.tab_dashboard, text=" 📊 Dashboard ")
        self.notebook.add(self.tab_patients, text=" 👤 Patient Registry ")
        self.notebook.add(self.tab_doctors, text=" 👨‍⚕️ Doctor Catalog ")
        self.notebook.add(self.tab_booking, text=" 📅 Book Appointment ")
        self.notebook.add(self.tab_appointments, text=" 📋 Appointment Ledger ")

        # Build each tab UI
        self._build_dashboard_tab()
        self._build_patients_tab()
        self._build_doctors_tab()
        self._build_booking_tab()
        self._build_appointments_tab()

    def _build_statusbar(self):
        """Bottom status bar."""
        self.statusbar = tk.Label(
            self,
            text="System Ready | Database Connected: hospital_registry.db",
            font=("Segoe UI", 9),
            bg="#e2e8f0",
            fg=self.TEXT_MUTED,
            anchor="w",
            padx=15,
            pady=4
        )
        self.statusbar.pack(fill="x", side="bottom")

    def _set_status(self, msg: str):
        self.statusbar.config(text=f"{msg} | System Time: {datetime.datetime.now().strftime('%H:%M:%S')}")

    # ==================== TAB 1: DASHBOARD ====================

    def _build_dashboard_tab(self):
        container = tk.Frame(self.tab_dashboard, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Stat Cards Container
        cards_frame = tk.Frame(container, bg=self.BG_MAIN)
        cards_frame.pack(fill="x", pady=(0, 15))

        self.card_patients_val = self._create_stat_card(cards_frame, "Registered Patients", "0", "#0284c7", 0)
        self.card_doctors_val = self._create_stat_card(cards_frame, "Active Doctors", "0", "#0d9488", 1)
        self.card_today_val = self._create_stat_card(cards_frame, "Today's Appointments", "0", "#d97706", 2)
        self.card_rev_val = self._create_stat_card(cards_frame, "Total Revenue (₹)", "₹ 0.00", "#16a34a", 3)

        # Quick Actions & Schedule Overview Split
        content_frame = tk.Frame(container, bg=self.BG_MAIN)
        content_frame.pack(fill="both", expand=True)

        # Left: Quick Actions
        actions_card = tk.LabelFrame(content_frame, text=" Quick Actions ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=15, pady=15)
        actions_card.pack(side="left", fill="y", padx=(0, 10))

        btn1 = ttk.Button(actions_card, text="➕ Book New Appointment", style="Accent.TButton", command=lambda: self.notebook.select(self.tab_booking))
        btn1.pack(fill="x", pady=6)

        btn2 = ttk.Button(actions_card, text="👤 Register Patient", style="Secondary.TButton", command=lambda: self.notebook.select(self.tab_patients))
        btn2.pack(fill="x", pady=6)

        btn3 = ttk.Button(actions_card, text="👨‍⚕️ Manage Doctors", style="Secondary.TButton", command=lambda: self.notebook.select(self.tab_doctors))
        btn3.pack(fill="x", pady=6)

        btn4 = ttk.Button(actions_card, text="🔄 Refresh Dashboard", style="Secondary.TButton", command=self._refresh_all_data)
        btn4.pack(fill="x", pady=6)

        btn5 = ttk.Button(actions_card, text="🌱 Re-Seed Sample Data", style="Danger.TButton", command=self._handle_reseed)
        btn5.pack(fill="x", pady=(20, 6))

        # Right: Today & Upcoming Schedule
        schedule_card = tk.LabelFrame(content_frame, text=" Today's & Upcoming Hospital Schedule ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=10, pady=10)
        schedule_card.pack(side="right", fill="both", expand=True)

        cols = ("Code", "Patient", "Doctor", "Specialization", "Date", "Slot", "Status", "Fee")
        self.dash_tree = ttk.Treeview(schedule_card, columns=cols, show="headings", height=12)

        self.dash_tree.heading("Code", text="Code")
        self.dash_tree.heading("Patient", text="Patient")
        self.dash_tree.heading("Doctor", text="Doctor")
        self.dash_tree.heading("Specialization", text="Specialization")
        self.dash_tree.heading("Date", text="Date")
        self.dash_tree.heading("Slot", text="Slot")
        self.dash_tree.heading("Status", text="Status")
        self.dash_tree.heading("Fee", text="Fee (₹)")

        self.dash_tree.column("Code", width=110, anchor="center")
        self.dash_tree.column("Patient", width=140)
        self.dash_tree.column("Doctor", width=150)
        self.dash_tree.column("Specialization", width=130)
        self.dash_tree.column("Date", width=90, anchor="center")
        self.dash_tree.column("Slot", width=110, anchor="center")
        self.dash_tree.column("Status", width=90, anchor="center")
        self.dash_tree.column("Fee", width=90, anchor="e")

        dash_scroll = ttk.Scrollbar(schedule_card, orient="vertical", command=self.dash_tree.yview)
        self.dash_tree.configure(yscrollcommand=dash_scroll.set)

        self.dash_tree.pack(side="left", fill="both", expand=True)
        dash_scroll.pack(side="right", fill="y")

    def _create_stat_card(self, parent, title: str, initial_val: str, accent_color: str, col_idx: int) -> tk.Label:
        card = tk.Frame(parent, bg=self.CARD_BG, highlightbackground=self.CARD_BORDER, highlightthickness=1)
        card.grid(row=0, column=col_idx, sticky="nsew", padx=5)
        parent.columnconfigure(col_idx, weight=1)

        accent_bar = tk.Frame(card, bg=accent_color, height=4)
        accent_bar.pack(fill="x", side="top")

        t_lbl = tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg=self.TEXT_MUTED)
        t_lbl.pack(anchor="w", padx=12, pady=(10, 2))

        v_lbl = tk.Label(card, text=initial_val, font=("Segoe UI", 16, "bold"), bg=self.CARD_BG, fg=accent_color)
        v_lbl.pack(anchor="w", padx=12, pady=(0, 10))

        return v_lbl

    # ==================== TAB 2: PATIENT REGISTRY ====================

    def _build_patients_tab(self):
        container = tk.Frame(self.tab_patients, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Left Form Frame
        form_frame = tk.LabelFrame(container, text=" Patient Registration Form ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=15, pady=15)
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        self.pat_vars = {}
        row = 0

        # Patient Code (Auto Generated)
        tk.Label(form_frame, text="Patient Code:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_code_var"] = tk.StringVar(value="PAT-Auto")
        e_code = ttk.Entry(form_frame, textvariable=self.pat_vars["pat_code_var"], state="readonly", width=25)
        e_code.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Full Name (with character validation)
        tk.Label(form_frame, text="Full Name *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_name_var"] = tk.StringVar()
        e_name = ttk.Entry(form_frame, textvariable=self.pat_vars["pat_name_var"], width=25, validate="key", validatecommand=self.vcmd_name)
        e_name.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Age (Digits only validator)
        tk.Label(form_frame, text="Age * (1-120):", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_age_var"] = tk.StringVar(value="30")
        e_age = ttk.Spinbox(form_frame, from_=1, to=120, textvariable=self.pat_vars["pat_age_var"], width=23, validate="key", validatecommand=self.vcmd_digits)
        e_age.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Gender
        tk.Label(form_frame, text="Gender *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_gender_var"] = tk.StringVar(value="Male")
        gender_cb = ttk.Combobox(form_frame, textvariable=self.pat_vars["pat_gender_var"], values=["Male", "Female", "Other"], state="readonly", width=23)
        gender_cb.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Phone (Numeric / Phone chars validator)
        tk.Label(form_frame, text="Phone (+91) *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_phone_var"] = tk.StringVar(value="+91 ")
        e_phone = ttk.Entry(form_frame, textvariable=self.pat_vars["pat_phone_var"], width=25, validate="key", validatecommand=self.vcmd_phone)
        e_phone.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Email
        tk.Label(form_frame, text="Email Address:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_email_var"] = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.pat_vars["pat_email_var"], width=25).grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Blood Group
        tk.Label(form_frame, text="Blood Group *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=4)
        self.pat_vars["pat_blood_var"] = tk.StringVar(value="O+")
        blood_cb = ttk.Combobox(form_frame, textvariable=self.pat_vars["pat_blood_var"], values=DatabaseManager.BLOOD_GROUPS, state="readonly", width=23)
        blood_cb.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Address
        tk.Label(form_frame, text="Address:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="nw", pady=4)
        self.pat_address_txt = tk.Text(form_frame, width=24, height=3, font=("Segoe UI", 9))
        self.pat_address_txt.grid(row=row, column=1, sticky="w", pady=4, padx=5)
        row += 1

        # Action Buttons
        btn_frame = tk.Frame(form_frame, bg=self.CARD_BG)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(15, 0), sticky="ew")

        ttk.Button(btn_frame, text="💾 Save Patient", style="Accent.TButton", command=self._save_patient).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🧹 Clear", style="Secondary.TButton", command=self._clear_patient_form).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Delete", style="Danger.TButton", command=self._delete_patient).pack(side="left", padx=2)

        # Right Directory Frame
        list_frame = tk.LabelFrame(container, text=" Registered Patients Directory ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=10, pady=10)
        list_frame.pack(side="right", fill="both", expand=True)

        # Search Bar
        search_bar = tk.Frame(list_frame, bg=self.CARD_BG)
        search_bar.pack(fill="x", pady=(0, 10))

        tk.Label(search_bar, text="🔍 Search Patient:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).pack(side="left", padx=(0, 5))
        self.pat_search_var = tk.StringVar()
        self.pat_search_var.trace_add("write", lambda *args: self._refresh_patients_table())
        ttk.Entry(search_bar, textvariable=self.pat_search_var, width=30).pack(side="left", padx=5)

        # Table
        p_cols = ("ID", "Code", "Name", "Age", "Gender", "Phone", "Blood", "Address")
        self.pat_tree = ttk.Treeview(list_frame, columns=p_cols, show="headings", height=15)

        for c in p_cols:
            self.pat_tree.heading(c, text=c)

        self.pat_tree.column("ID", width=40, anchor="center")
        self.pat_tree.column("Code", width=80, anchor="center")
        self.pat_tree.column("Name", width=140)
        self.pat_tree.column("Age", width=45, anchor="center")
        self.pat_tree.column("Gender", width=65, anchor="center")
        self.pat_tree.column("Phone", width=120)
        self.pat_tree.column("Blood", width=55, anchor="center")
        self.pat_tree.column("Address", width=180)

        p_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.pat_tree.yview)
        self.pat_tree.configure(yscrollcommand=p_scroll.set)

        self.pat_tree.pack(side="left", fill="both", expand=True)
        p_scroll.pack(side="right", fill="y")

        self.pat_tree.bind("<<TreeviewSelect>>", self._on_patient_selected)

    def _save_patient(self):
        name = self.pat_vars["pat_name_var"].get().strip()
        age_str = self.pat_vars["pat_age_var"].get().strip()
        gender = self.pat_vars["pat_gender_var"].get().strip()
        phone = self.pat_vars["pat_phone_var"].get().strip()
        email = self.pat_vars["pat_email_var"].get().strip()
        blood = self.pat_vars["pat_blood_var"].get().strip()
        address = self.pat_address_txt.get("1.0", tk.END).strip()

        # Mandatory checks
        if not name or not age_str or not phone:
            messagebox.showerror("Type Validation Error", "Please fill in all mandatory fields (Name, Age, Phone).")
            return

        # Name type validation
        if not is_valid_name(name):
            messagebox.showerror("Type Validation Error", "Invalid Patient Name! Name should only contain alphabetic letters and spaces.")
            return

        # Age type validation
        try:
            age = int(age_str)
            if age <= 0 or age > 120:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Type Validation Error", "Invalid Age! Age must be a numerical integer between 1 and 120.")
            return

        # Phone type validation
        if not is_valid_phone(phone):
            messagebox.showerror("Type Validation Error", "Invalid Phone Number! Phone number must contain numerical digits (e.g. +91 9811122334).")
            return

        # Email type validation
        if email and not is_valid_email(email):
            messagebox.showerror("Type Validation Error", "Invalid Email Address! Please enter a valid email address format (e.g., patient@domain.com).")
            return

        patient = Patient(
            patient_id=self.selected_patient_id,
            patient_code=self.pat_vars["pat_code_var"].get() if self.selected_patient_id else None,
            name=name,
            age=age,
            gender=gender,
            phone=phone,
            email=email,
            blood_group=blood,
            address=address
        )

        try:
            if self.selected_patient_id:
                db_result = self.db.update_patient(patient)
                if db_result:
                    messagebox.showinfo("Success", f"Patient profile '{name}' updated successfully.")
            else:
                p_id, code = self.db.add_patient(patient)
                messagebox.showinfo("Success", f"Patient registered successfully!\nAssigned Patient Code: {code}")

            self._clear_patient_form()
            self._refresh_all_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def _on_patient_selected(self, event):
        sel = self.pat_tree.selection()
        if not sel:
            return
        item = self.pat_tree.item(sel[0])
        vals = item["values"]
        if not vals:
            return

        self.selected_patient_id = int(vals[0])
        self.pat_vars["pat_code_var"].set(vals[1])
        self.pat_vars["pat_name_var"].set(vals[2])
        self.pat_vars["pat_age_var"].set(vals[3])
        self.pat_vars["pat_gender_var"].set(vals[4])
        self.pat_vars["pat_phone_var"].set(vals[5])

        # retrieve detailed patient
        patients = [p for p in self.db.get_all_patients() if p.id == self.selected_patient_id]
        if patients:
            p = patients[0]
            self.pat_vars["pat_email_var"].set(p.email or "")
            self.pat_vars["pat_blood_var"].set(p.blood_group or "O+")
            self.pat_address_txt.delete("1.0", tk.END)
            self.pat_address_txt.insert("1.0", p.address or "")

    def _clear_patient_form(self):
        self.selected_patient_id = None
        self.pat_vars["pat_code_var"].set("PAT-Auto")
        self.pat_vars["pat_name_var"].set("")
        self.pat_vars["pat_age_var"].set("30")
        self.pat_vars["pat_gender_var"].set("Male")
        self.pat_vars["pat_phone_var"].set("+91 ")
        self.pat_vars["pat_email_var"].set("")
        self.pat_vars["pat_blood_var"].set("O+")
        self.pat_address_txt.delete("1.0", tk.END)
        self.pat_tree.selection_remove(self.pat_tree.selection())

    def _delete_patient(self):
        if not self.selected_patient_id:
            messagebox.showwarning("Select Patient", "Please select a patient from the table to delete.")
            return

        name = self.pat_vars["pat_name_var"].get()
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete patient '{name}'?\nThis will also remove associated appointment records."):
            if self.db.delete_patient(self.selected_patient_id):
                messagebox.showinfo("Deleted", "Patient record deleted successfully.")
                self._clear_patient_form()
                self._refresh_all_data()

    # ==================== TAB 3: DOCTOR CATALOG ====================

    def _build_doctors_tab(self):
        container = tk.Frame(self.tab_doctors, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Top Doctor Form
        form_frame = tk.LabelFrame(container, text=" Doctor Profile Management ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=15, pady=10)
        form_frame.pack(fill="x", pady=(0, 10))

        f_inner = tk.Frame(form_frame, bg=self.CARD_BG)
        f_inner.pack(fill="x")

        self.doc_vars = {
            "name": tk.StringVar(),
            "spec": tk.StringVar(value="General Medicine"),
            "fee": tk.StringVar(value="500"),
            "phone": tk.StringVar(value="+91 "),
            "email": tk.StringVar(),
            "days": tk.StringVar(value="Mon-Fri")
        }

        specs = ["General Medicine", "Cardiology", "Pediatrics", "Orthopedics", "Gynecology & Obstetrics", "Dermatology", "Neurology", "ENT", "Ophthalmology"]

        # Row 1
        tk.Label(f_inner, text="Doctor Name *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(f_inner, textvariable=self.doc_vars["name"], width=25, validate="key", validatecommand=self.vcmd_name).grid(row=0, column=1, sticky="w", pady=4, padx=8)

        tk.Label(f_inner, text="Specialization *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=0, column=2, sticky="w", pady=4)
        ttk.Combobox(f_inner, textvariable=self.doc_vars["spec"], values=specs, width=23).grid(row=0, column=3, sticky="w", pady=4, padx=8)

        tk.Label(f_inner, text="Consultation Fee (₹) *:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG, fg="#0f766e").grid(row=0, column=4, sticky="w", pady=4)
        ttk.Entry(f_inner, textvariable=self.doc_vars["fee"], width=15, validate="key", validatecommand=self.vcmd_decimal).grid(row=0, column=5, sticky="w", pady=4, padx=8)

        # Row 2
        tk.Label(f_inner, text="Phone (+91) *:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(f_inner, textvariable=self.doc_vars["phone"], width=25, validate="key", validatecommand=self.vcmd_phone).grid(row=1, column=1, sticky="w", pady=4, padx=8)

        tk.Label(f_inner, text="Email Address:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=1, column=2, sticky="w", pady=4)
        ttk.Entry(f_inner, textvariable=self.doc_vars["email"], width=25).grid(row=1, column=3, sticky="w", pady=4, padx=8)

        tk.Label(f_inner, text="Available Days:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=1, column=4, sticky="w", pady=4)
        ttk.Entry(f_inner, textvariable=self.doc_vars["days"], width=15).grid(row=1, column=5, sticky="w", pady=4, padx=8)

        # Doctor Buttons
        btn_bar = tk.Frame(form_frame, bg=self.CARD_BG)
        btn_bar.pack(fill="x", pady=(10, 0))

        ttk.Button(btn_bar, text="💾 Save Doctor", style="Accent.TButton", command=self._save_doctor).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🧹 Clear Form", style="Secondary.TButton", command=self._clear_doctor_form).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="🗑️ Delete Doctor", style="Danger.TButton", command=self._delete_doctor).pack(side="left", padx=4)

        # Doctor Table
        list_frame = tk.LabelFrame(container, text=" Hospital Doctor Directory ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=10, pady=10)
        list_frame.pack(fill="both", expand=True)

        d_cols = ("ID", "Doctor Name", "Specialization", "Fee (₹)", "Phone", "Email", "Available Days")
        self.doc_tree = ttk.Treeview(list_frame, columns=d_cols, show="headings", height=10)

        for c in d_cols:
            self.doc_tree.heading(c, text=c)

        self.doc_tree.column("ID", width=40, anchor="center")
        self.doc_tree.column("Doctor Name", width=180)
        self.doc_tree.column("Specialization", width=160)
        self.doc_tree.column("Fee (₹)", width=100, anchor="e")
        self.doc_tree.column("Phone", width=130)
        self.doc_tree.column("Email", width=180)
        self.doc_tree.column("Available Days", width=110, anchor="center")

        d_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.doc_tree.yview)
        self.doc_tree.configure(yscrollcommand=d_scroll.set)

        self.doc_tree.pack(side="left", fill="both", expand=True)
        d_scroll.pack(side="right", fill="y")

        self.doc_tree.bind("<<TreeviewSelect>>", self._on_doctor_selected)

    def _save_doctor(self):
        name = self.doc_vars["name"].get().strip()
        spec = self.doc_vars["spec"].get().strip()
        fee_str = self.doc_vars["fee"].get().strip()
        phone = self.doc_vars["phone"].get().strip()
        email = self.doc_vars["email"].get().strip()
        days = self.doc_vars["days"].get().strip()

        if not name or not spec or not fee_str or not phone:
            messagebox.showerror("Type Validation Error", "Please fill in all mandatory doctor details.")
            return

        # Name type validation
        if not is_valid_name(name):
            messagebox.showerror("Type Validation Error", "Invalid Doctor Name! Name should contain only alphabetic letters, spaces, and titles.")
            return

        # Fee type validation
        try:
            fee = float(fee_str.replace("₹", "").replace(",", "").strip())
            if fee < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Type Validation Error", "Invalid Consultation Fee! Fee must be a positive numerical value in Rupees (₹).")
            return

        # Phone type validation
        if not is_valid_phone(phone):
            messagebox.showerror("Type Validation Error", "Invalid Doctor Phone Number! Phone number must contain numerical digits.")
            return

        # Email type validation
        if email and not is_valid_email(email):
            messagebox.showerror("Type Validation Error", "Invalid Email Address! Please enter a valid doctor email format.")
            return

        doctor = Doctor(
            doctor_id=self.selected_doctor_id,
            name=name,
            specialization=spec,
            fee_inr=fee,
            phone=phone,
            email=email,
            available_days=days
        )

        try:
            if self.selected_doctor_id:
                if self.db.update_doctor(doctor):
                    messagebox.showinfo("Success", f"Doctor '{name}' details updated successfully.")
            else:
                self.db.add_doctor(doctor)
                messagebox.showinfo("Success", f"Doctor '{name}' registered successfully.")

            self._clear_doctor_form()
            self._refresh_all_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def _on_doctor_selected(self, event):
        sel = self.doc_tree.selection()
        if not sel:
            return
        item = self.doc_tree.item(sel[0])
        vals = item["values"]
        if not vals:
            return

        self.selected_doctor_id = int(vals[0])
        self.doc_vars["name"].set(vals[1])
        self.doc_vars["spec"].set(vals[2])
        # clean fee format
        fee_clean = str(vals[3]).replace("₹", "").replace(",", "").strip()
        self.doc_vars["fee"].set(fee_clean)
        self.doc_vars["phone"].set(vals[4])
        self.doc_vars["email"].set(vals[5])
        self.doc_vars["days"].set(vals[6])

    def _clear_doctor_form(self):
        self.selected_doctor_id = None
        self.doc_vars["name"].set("")
        self.doc_vars["spec"].set("General Medicine")
        self.doc_vars["fee"].set("500")
        self.doc_vars["phone"].set("+91 ")
        self.doc_vars["email"].set("")
        self.doc_vars["days"].set("Mon-Fri")
        self.doc_tree.selection_remove(self.doc_tree.selection())

    def _delete_doctor(self):
        if not self.selected_doctor_id:
            messagebox.showwarning("Select Doctor", "Please select a doctor to delete.")
            return

        name = self.doc_vars["name"].get()
        if messagebox.askyesno("Confirm Delete", f"Delete doctor '{name}'?\nAssociated appointments will also be removed."):
            if self.db.delete_doctor(self.selected_doctor_id):
                messagebox.showinfo("Deleted", "Doctor profile removed successfully.")
                self._clear_doctor_form()
                self._refresh_all_data()

    # ==================== TAB 4: BOOK APPOINTMENT (WITH SQL DOUBLE BOOKING CHECK) ====================

    def _build_booking_tab(self):
        container = tk.Frame(self.tab_booking, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Left Booking Entry Form
        form_frame = tk.LabelFrame(container, text=" Book Patient Appointment ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=15, pady=15)
        form_frame.pack(side="left", fill="y", padx=(0, 10))

        row = 0

        # Patient Selector
        tk.Label(form_frame, text="Select Patient *:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=6)
        self.book_patient_cb = ttk.Combobox(form_frame, width=32, state="readonly")
        self.book_patient_cb.grid(row=row, column=1, sticky="w", pady=6, padx=5)
        row += 1

        # Doctor Selector
        tk.Label(form_frame, text="Select Doctor *:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=6)
        self.book_doctor_cb = ttk.Combobox(form_frame, width=32, state="readonly")
        self.book_doctor_cb.grid(row=row, column=1, sticky="w", pady=6, padx=5)
        self.book_doctor_cb.bind("<<ComboboxSelected>>", self._on_booking_doctor_changed)
        row += 1

        # Date Picker Entry
        tk.Label(form_frame, text="Appointment Date * (YYYY-MM-DD):", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=6)
        date_f = tk.Frame(form_frame, bg=self.CARD_BG)
        date_f.grid(row=row, column=1, sticky="w", pady=6, padx=5)

        self.book_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.book_date_var.trace_add("write", lambda *args: self._update_slot_availability_matrix())
        ttk.Entry(date_f, textvariable=self.book_date_var, width=18).pack(side="left")
        ttk.Button(date_f, text="Today", style="Secondary.TButton", command=lambda: self.book_date_var.set(datetime.date.today().strftime("%Y-%m-%d"))).pack(side="left", padx=4)
        row += 1

        # Time Slot Selector
        tk.Label(form_frame, text="Hourly Time Slot *:", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=6)
        self.book_slot_cb = ttk.Combobox(form_frame, values=DatabaseManager.TIME_SLOTS, width=32, state="readonly")
        self.book_slot_cb.set(DatabaseManager.TIME_SLOTS[0])
        self.book_slot_cb.grid(row=row, column=1, sticky="w", pady=6, padx=5)
        row += 1

        # Consultation Fee Display
        tk.Label(form_frame, text="Consultation Fee (₹):", font=("Segoe UI", 9, "bold"), bg=self.CARD_BG).grid(row=row, column=0, sticky="w", pady=6)
        self.book_fee_lbl = tk.Label(form_frame, text="₹ 0.00", font=("Segoe UI", 12, "bold"), bg=self.CARD_BG, fg="#0f766e")
        self.book_fee_lbl.grid(row=row, column=1, sticky="w", pady=6, padx=5)
        row += 1

        # Notes
        tk.Label(form_frame, text="Clinical Notes:", font=("Segoe UI", 9), bg=self.CARD_BG).grid(row=row, column=0, sticky="nw", pady=6)
        self.book_notes_txt = tk.Text(form_frame, width=30, height=4, font=("Segoe UI", 9))
        self.book_notes_txt.grid(row=row, column=1, sticky="w", pady=6, padx=5)
        row += 1

        # Book Button
        btn_f = tk.Frame(form_frame, bg=self.CARD_BG)
        btn_f.grid(row=row, column=0, columnspan=2, pady=(15, 0), sticky="ew")

        ttk.Button(btn_f, text="⚡ Confirm Booking (Check SQL)", style="Accent.TButton", command=self._handle_book_appointment).pack(fill="x")

        # Right Slot Availability Matrix Frame
        right_frame = tk.LabelFrame(container, text=" Live Doctor Time-Slot Availability Matrix ", font=("Segoe UI", 11, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=15, pady=15)
        right_frame.pack(side="right", fill="both", expand=True)

        info_lbl = tk.Label(
            right_frame,
            text="SQL Query Enforcement: Red slots indicate existing booked appointments.\nGreen slots are currently available for selection.",
            font=("Segoe UI", 9, "italic"),
            bg=self.CARD_BG,
            fg=self.TEXT_MUTED,
            justify="left"
        )
        info_lbl.pack(anchor="w", pady=(0, 10))

        # Matrix Canvas/Scroll Frame
        self.matrix_container = tk.Frame(right_frame, bg=self.CARD_BG)
        self.matrix_container.pack(fill="both", expand=True)

    def _on_booking_doctor_changed(self, event=None):
        doc_str = self.book_doctor_cb.get()
        if not doc_str:
            self.book_fee_lbl.config(text="₹ 0.00")
            return
        # Extract doctor ID
        doc_id = int(doc_str.split(" (ID: ")[1].split(")")[0])
        doctor = self.db.get_doctor_by_id(doc_id)
        if doctor:
            self.book_fee_lbl.config(text=doctor.fee_formatted)

        self._update_slot_availability_matrix()

    def _update_slot_availability_matrix(self):
        # Clear previous matrix
        for widget in self.matrix_container.winfo_children():
            widget.destroy()

        doc_str = self.book_doctor_cb.get()
        date_str = self.book_date_var.get().strip()

        if not doc_str or not date_str or not is_valid_date(date_str):
            tk.Label(self.matrix_container, text="Select a Doctor and valid Date (YYYY-MM-DD) to inspect schedule.", bg=self.CARD_BG, fg=self.TEXT_MUTED).pack(pady=20)
            return

        try:
            doc_id = int(doc_str.split(" (ID: ")[1].split(")")[0])
        except Exception:
            return

        tk.Label(self.matrix_container, text=f"Hourly Schedule for {doc_str.split(' (ID:')[0]} on {date_str}:", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG).pack(anchor="w", pady=(0, 10))

        slots_grid = tk.Frame(self.matrix_container, bg=self.CARD_BG)
        slots_grid.pack(fill="x")

        for idx, slot in enumerate(DatabaseManager.TIME_SLOTS):
            is_booked = self.db.is_doctor_booked(doc_id, date_str, slot)
            
            slot_card = tk.Frame(
                slots_grid,
                bg="#fee2e2" if is_booked else "#dcfce7",
                highlightbackground="#f87171" if is_booked else "#4ade80",
                highlightthickness=1,
                padx=8,
                pady=8
            )
            slot_card.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)
            slots_grid.columnconfigure(idx % 2, weight=1)

            t_lbl = tk.Label(slot_card, text=slot, font=("Segoe UI", 9, "bold"), bg="#fee2e2" if is_booked else "#dcfce7")
            t_lbl.pack(anchor="w")

            status_lbl = tk.Label(
                slot_card,
                text="🔴 BOOKED (SQL Conflict)" if is_booked else "🟢 AVAILABLE",
                font=("Segoe UI", 8, "bold"),
                bg="#fee2e2" if is_booked else "#dcfce7",
                fg="#991b1b" if is_booked else "#166534"
            )
            status_lbl.pack(anchor="w")

    def _handle_book_appointment(self):
        pat_str = self.book_patient_cb.get()
        doc_str = self.book_doctor_cb.get()
        date_str = self.book_date_var.get().strip()
        slot = self.book_slot_cb.get().strip()
        notes = self.book_notes_txt.get("1.0", tk.END).strip()

        if not pat_str or not doc_str or not date_str or not slot:
            messagebox.showerror("Type Validation Error", "Please select a patient, doctor, appointment date, and time slot.")
            return

        # Date type validation
        if not is_valid_date(date_str):
            messagebox.showerror("Type Validation Error", "Invalid Appointment Date! Date must be in YYYY-MM-DD format (e.g. 2026-08-15).")
            return

        try:
            pat_id = int(pat_str.split(" (Code: ")[1].split(")")[0])
            doc_id = int(doc_str.split(" (ID: ")[1].split(")")[0])
        except Exception:
            messagebox.showerror("Error", "Invalid patient or doctor selection.")
            return

        appointment = Appointment(
            patient_id=pat_id,
            doctor_id=doc_id,
            appointment_date=date_str,
            time_slot=slot,
            status="Scheduled",
            notes=notes
        )

        try:
            # This triggers SQL check and raises ValueError if double-booked!
            apt_id, code = self.db.book_appointment(appointment)
            
            messagebox.showinfo(
                "Appointment Confirmed! 🎯",
                f"Appointment booked successfully!\n\n"
                f"Booking Code: {code}\n"
                f"Date: {date_str}\n"
                f"Time Slot: {slot}\n"
                f"Consultation Fee: {self.book_fee_lbl.cget('text')}"
            )
            self._update_slot_availability_matrix()
            self._refresh_all_data()
        except ValueError as val_err:
            # Double-booking or patient conflict error box!
            messagebox.showerror("SQL Double-Booking Conflict Alert 🚫", str(val_err))
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # ==================== TAB 5: APPOINTMENT LEDGER ====================

    def _build_appointments_tab(self):
        container = tk.Frame(self.tab_appointments, bg=self.BG_MAIN)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        # Filters Bar
        filter_card = tk.LabelFrame(container, text=" Filter & Search Appointments ", font=("Segoe UI", 10, "bold"), bg=self.CARD_BG, fg=self.HEADER_BG, padx=10, pady=8)
        filter_card.pack(fill="x", pady=(0, 10))

        tk.Label(filter_card, text="Doctor:", font=("Segoe UI", 9), bg=self.CARD_BG).pack(side="left", padx=(0, 4))
        self.apt_filter_doc_cb = ttk.Combobox(filter_card, width=22, state="readonly")
        self.apt_filter_doc_cb.pack(side="left", padx=4)
        self.apt_filter_doc_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_appointments_table())

        tk.Label(filter_card, text="Date (YYYY-MM-DD):", font=("Segoe UI", 9), bg=self.CARD_BG).pack(side="left", padx=(10, 4))
        self.apt_filter_date_var = tk.StringVar()
        self.apt_filter_date_var.trace_add("write", lambda *args: self._refresh_appointments_table())
        ttk.Entry(filter_card, textvariable=self.apt_filter_date_var, width=12).pack(side="left", padx=4)

        tk.Label(filter_card, text="Status:", font=("Segoe UI", 9), bg=self.CARD_BG).pack(side="left", padx=(10, 4))
        self.apt_filter_status_cb = ttk.Combobox(filter_card, values=["All", "Scheduled", "Completed", "Cancelled"], width=12, state="readonly")
        self.apt_filter_status_cb.set("All")
        self.apt_filter_status_cb.pack(side="left", padx=4)
        self.apt_filter_status_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_appointments_table())

        tk.Label(filter_card, text="Search:", font=("Segoe UI", 9), bg=self.CARD_BG).pack(side="left", padx=(10, 4))
        self.apt_filter_search_var = tk.StringVar()
        self.apt_filter_search_var.trace_add("write", lambda *args: self._refresh_appointments_table())
        ttk.Entry(filter_card, textvariable=self.apt_filter_search_var, width=18).pack(side="left", padx=4)

        ttk.Button(filter_card, text="Reset Filters", style="Secondary.TButton", command=self._reset_apt_filters).pack(side="right", padx=5)

        # Appointments Table
        table_frame = tk.Frame(container, bg=self.CARD_BG)
        table_frame.pack(fill="both", expand=True)

        a_cols = ("ID", "Code", "Patient Name", "Doctor Name", "Specialization", "Date", "Slot", "Status", "Fee (₹)", "Notes")
        self.apt_tree = ttk.Treeview(table_frame, columns=a_cols, show="headings", height=14)

        for c in a_cols:
            self.apt_tree.heading(c, text=c)

        self.apt_tree.column("ID", width=40, anchor="center")
        self.apt_tree.column("Code", width=110, anchor="center")
        self.apt_tree.column("Patient Name", width=140)
        self.apt_tree.column("Doctor Name", width=150)
        self.apt_tree.column("Specialization", width=130)
        self.apt_tree.column("Date", width=90, anchor="center")
        self.apt_tree.column("Slot", width=110, anchor="center")
        self.apt_tree.column("Status", width=90, anchor="center")
        self.apt_tree.column("Fee (₹)", width=90, anchor="e")
        self.apt_tree.column("Notes", width=180)

        a_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.apt_tree.yview)
        self.apt_tree.configure(yscrollcommand=a_scroll.set)

        self.apt_tree.pack(side="left", fill="both", expand=True)
        a_scroll.pack(side="right", fill="y")

        # Table Action Buttons Bar
        act_bar = tk.Frame(container, bg=self.BG_MAIN)
        act_bar.pack(fill="x", pady=(10, 0))

        ttk.Button(act_bar, text="✅ Mark Completed", style="Accent.TButton", command=lambda: self._update_apt_status("Completed")).pack(side="left", padx=4)
        ttk.Button(act_bar, text="❌ Cancel Appointment", style="Danger.TButton", command=lambda: self._update_apt_status("Cancelled")).pack(side="left", padx=4)
        ttk.Button(act_bar, text="🔄 Reschedule Slot", style="Secondary.TButton", command=self._reschedule_dialog).pack(side="left", padx=4)
        ttk.Button(act_bar, text="🧾 Print Consultation Slip", style="Secondary.TButton", command=self._print_slip_dialog).pack(side="left", padx=4)
        ttk.Button(act_bar, text="🗑️ Delete Record", style="Danger.TButton", command=self._delete_appointment).pack(side="right", padx=4)

    def _reset_apt_filters(self):
        self.apt_filter_doc_cb.set("")
        self.apt_filter_date_var.set("")
        self.apt_filter_status_cb.set("All")
        self.apt_filter_search_var.set("")
        self._refresh_appointments_table()

    def _update_apt_status(self, status: str):
        sel = self.apt_tree.selection()
        if not sel:
            messagebox.showwarning("Select Appointment", "Please select an appointment from the table.")
            return

        item = self.apt_tree.item(sel[0])
        apt_id = int(item["values"][0])
        code = item["values"][1]

        if self.db.update_appointment_status(apt_id, status):
            messagebox.showinfo("Status Updated", f"Appointment {code} status set to '{status}'.")
            self._refresh_all_data()

    def _delete_appointment(self):
        sel = self.apt_tree.selection()
        if not sel:
            messagebox.showwarning("Select Appointment", "Please select an appointment record to delete.")
            return

        item = self.apt_tree.item(sel[0])
        apt_id = int(item["values"][0])
        code = item["values"][1]

        if messagebox.askyesno("Confirm Delete", f"Delete appointment record {code}?"):
            if self.db.delete_appointment(apt_id):
                messagebox.showinfo("Deleted", "Appointment record deleted successfully.")
                self._refresh_all_data()

    def _reschedule_dialog(self):
        sel = self.apt_tree.selection()
        if not sel:
            messagebox.showwarning("Select Appointment", "Please select an appointment to reschedule.")
            return

        item = self.apt_tree.item(sel[0])
        apt_id = int(item["values"][0])
        code = item["values"][1]
        curr_date = item["values"][5]
        curr_slot = item["values"][6]

        dlg = tk.Toplevel(self)
        dlg.title(f"Reschedule Appointment {code}")
        dlg.geometry("380x240")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text=f"Reschedule {code}", font=("Segoe UI", 11, "bold"), fg=self.HEADER_BG).pack(pady=10)

        f = tk.Frame(dlg)
        f.pack(pady=10)

        tk.Label(f, text="New Date (YYYY-MM-DD):").grid(row=0, column=0, sticky="w", pady=5)
        d_var = tk.StringVar(value=curr_date)
        ttk.Entry(f, textvariable=d_var, width=18).grid(row=0, column=1, pady=5, padx=5)

        tk.Label(f, text="New Time Slot:").grid(row=1, column=0, sticky="w", pady=5)
        s_cb = ttk.Combobox(f, values=DatabaseManager.TIME_SLOTS, width=16, state="readonly")
        s_cb.set(curr_slot)
        s_cb.grid(row=1, column=1, pady=5, padx=5)

        def save_reschedule():
            new_date = d_var.get().strip()
            new_slot = s_cb.get().strip()

            if not is_valid_date(new_date):
                messagebox.showerror("Type Validation Error", "Invalid Reschedule Date! Must be YYYY-MM-DD format.")
                return

            try:
                self.db.reschedule_appointment(apt_id, new_date, new_slot)
                messagebox.showinfo("Success", f"Appointment rescheduled to {new_date} at {new_slot}.")
                dlg.destroy()
                self._refresh_all_data()
            except ValueError as val_err:
                messagebox.showerror("Reschedule Conflict Alert 🚫", str(val_err))
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dlg, text="Save Rescheduled Slot", style="Accent.TButton", command=save_reschedule).pack(pady=15)

    def _print_slip_dialog(self):
        sel = self.apt_tree.selection()
        if not sel:
            messagebox.showwarning("Select Appointment", "Please select an appointment to print consultation slip.")
            return

        item = self.apt_tree.item(sel[0])
        vals = item["values"]

        slip_txt = f"""
======================================================
         ST. JUDE SUPER SPECIALITY HOSPITAL
            PATIENT CONSULTATION SLIP
======================================================
Appointment Ref Code : {vals[1]}
Date                 : {vals[5]}
Time Slot            : {vals[6]}
Status               : {vals[7]}
------------------------------------------------------
PATIENT DETAILS:
Patient Name         : {vals[2]}

DOCTOR DETAILS:
Doctor Name          : {vals[3]}
Specialization       : {vals[4]}
Consultation Fee     : {vals[8]}
------------------------------------------------------
Clinical Notes / Instructions:
{vals[9] if vals[9] else 'None'}
======================================================
   Thank you for choosing St. Jude Hospital!
======================================================
"""

        dlg = tk.Toplevel(self)
        dlg.title(f"Consultation Slip - {vals[1]}")
        dlg.geometry("480x420")
        dlg.transient(self)

        txt_widget = tk.Text(dlg, font=("Courier New", 9), padx=10, pady=10)
        txt_widget.insert("1.0", slip_txt)
        txt_widget.config(state="disabled")
        txt_widget.pack(fill="both", expand=True)

    # ==================== DATA REFRESHING ====================

    def _refresh_all_data(self):
        """Refreshes all statistics, dropdowns, and tables across all tabs."""
        # 1. Dashboard Stats
        stats = self.db.get_dashboard_stats()
        self.card_patients_val.config(text=str(stats["total_patients"]))
        self.card_doctors_val.config(text=str(stats["total_doctors"]))
        self.card_today_val.config(text=str(stats["today_appointments"]))
        self.card_rev_val.config(text=stats["revenue_formatted"])

        # 2. Populate Dropdowns
        patients = self.db.get_all_patients()
        doctors = self.db.get_all_doctors()

        pat_options = [f"{p.name} (Code: {p.id})" for p in patients]
        self.book_patient_cb["values"] = pat_options
        if pat_options:
            self.book_patient_cb.set(pat_options[0])

        doc_options = [f"{d.name} - {d.specialization} (ID: {d.id})" for d in doctors]
        self.book_doctor_cb["values"] = doc_options
        if doc_options:
            self.book_doctor_cb.set(doc_options[0])
            self._on_booking_doctor_changed()

        filter_doc_options = [""] + doc_options
        self.apt_filter_doc_cb["values"] = filter_doc_options

        # 3. Refresh Tables
        self._refresh_dashboard_table()
        self._refresh_patients_table()
        self._refresh_doctors_table()
        self._refresh_appointments_table()
        self._update_slot_availability_matrix()
        self._set_status("All hospital records refreshed successfully.")

    def _refresh_dashboard_table(self):
        for item in self.dash_tree.get_children():
            self.dash_tree.delete(item)

        apts = self.db.get_all_appointments()[:15]  # Show recent 15
        for a in apts:
            self.dash_tree.insert("", "end", values=(
                a.appointment_code,
                a.patient_name,
                a.doctor_name,
                a.specialization,
                a.appointment_date,
                a.time_slot,
                a.status,
                a.fee_formatted
            ))

    def _refresh_patients_table(self):
        for item in self.pat_tree.get_children():
            self.pat_tree.delete(item)

        q = self.pat_search_var.get().strip()
        patients = self.db.search_patients(q) if q else self.db.get_all_patients()

        for p in patients:
            self.pat_tree.insert("", "end", values=(
                p.id,
                p.patient_code,
                p.name,
                p.age,
                p.gender,
                p.phone,
                p.blood_group,
                p.address
            ))

    def _refresh_doctors_table(self):
        for item in self.doc_tree.get_children():
            self.doc_tree.delete(item)

        doctors = self.db.get_all_doctors()
        for d in doctors:
            self.doc_tree.insert("", "end", values=(
                d.id,
                d.name,
                d.specialization,
                d.fee_formatted,
                d.phone,
                d.email,
                d.available_days
            ))

    def _refresh_appointments_table(self):
        for item in self.apt_tree.get_children():
            self.apt_tree.delete(item)

        doc_str = self.apt_filter_doc_cb.get()
        doc_id = None
        if doc_str and "(ID: " in doc_str:
            doc_id = int(doc_str.split(" (ID: ")[1].split(")")[0])

        date_str = self.apt_filter_date_var.get().strip()
        status = self.apt_filter_status_cb.get().strip()
        search_q = self.apt_filter_search_var.get().strip()

        apts = self.db.get_appointments_filtered(
            doctor_id=doc_id,
            date_str=date_str,
            status=status,
            search_query=search_q
        )

        for a in apts:
            self.apt_tree.insert("", "end", values=(
                a.id,
                a.appointment_code,
                a.patient_name,
                a.doctor_name,
                a.specialization,
                a.appointment_date,
                a.time_slot,
                a.status,
                a.fee_formatted,
                a.notes
            ))

    def _handle_reseed(self):
        if messagebox.askyesno("Confirm Re-Seed", "Re-seed hospital database with sample Indian patient & doctor records?"):
            seed_database(self.db, force=True)
            self._refresh_all_data()
            messagebox.showinfo("Seeded", "Sample data loaded successfully.")
