from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import re
import requests
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)
CORS(app)

load_dotenv()

# =========================================================
# FILE CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCEL_FILE = os.path.join(BASE_DIR, "registrations.xlsx")

REQUIRED_COLUMNS = [
    "Registration_ID",
    "Name",
    "Email",
    "Phone",
    "Domain",
    "Duration",
    "Status",
    "Created_At"
]

# =========================================================
# AVAILABLE DOMAINS
# =========================================================

DOMAINS = [
    "Data Science",
    "Data Analytics",
    "Artificial Intelligence",
    "Machine Learning",
    "Python Development",
    "Web Development",
    "Full Stack Development",
    "Java Development",
    "Cloud Computing",
    "Cyber Security",
    "Android Development"
]

# =========================================================
# EXCEL FUNCTIONS
# =========================================================

def initialize_excel():
    """
    Creates registrations.xlsx if it does not exist.
    """

    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
        df.to_excel(EXCEL_FILE, index=False)


def load_registrations():
    """
    Loads registration data from Excel.
    """

    initialize_excel()

    try:
        df = pd.read_excel(EXCEL_FILE)

        for column in REQUIRED_COLUMNS:
            if column not in df.columns:
                df[column] = ""

        return df[REQUIRED_COLUMNS]

    except Exception:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)


def save_registrations(df):
    """
    Saves registration data to Excel.
    """

    df.to_excel(EXCEL_FILE, index=False)


# =========================================================
# VALIDATION
# =========================================================

def validate_email(email):
    """
    Validates email address.
    """

    if not email:
        return False

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return re.match(pattern, email.strip()) is not None


def validate_phone(phone):
    """
    Validates Indian 10-digit mobile number.
    """

    if not phone:
        return False

    phone = re.sub(r"\D", "", str(phone))

    return bool(
        re.fullmatch(r"[6-9]\d{9}", phone)
    )


def clean_name(name):
    """
    Cleans and validates name.
    """

    if not name:
        return ""

    name = re.sub(r"\s+", " ", str(name)).strip()

    return name


# =========================================================
# DOMAIN EXTRACTION
# =========================================================

def get_domain(text):
    """
    Detects internship domain from user message.
    """

    if not text:
        return None

    text_lower = text.lower()

    # Exact domain names
    for domain in DOMAINS:

        if domain.lower() in text_lower:
            return domain

    # Common aliases
    aliases = {
        "ds": "Data Science",
        "data science": "Data Science",

        "da": "Data Analytics",
        "data analytics": "Data Analytics",

        "ai": "Artificial Intelligence",
        "artificial intelligence": "Artificial Intelligence",

        "ml": "Machine Learning",
        "machine learning": "Machine Learning",

        "python": "Python Development",

        "web": "Web Development",
        "web development": "Web Development",

        "full stack": "Full Stack Development",
        "fullstack": "Full Stack Development",

        "java": "Java Development",

        "cloud": "Cloud Computing",

        "cyber": "Cyber Security",
        "cyber security": "Cyber Security",

        "android": "Android Development"
    }

    for keyword, domain in aliases.items():

        if keyword in text_lower:
            return domain

    return None


# =========================================================
# DURATION EXTRACTION
# =========================================================

def get_duration(text):
    """
    Detects internship duration.
    """

    if not text:
        return None

    text = str(text).lower().strip()

    pattern = r"\b\d+\s+(?:days?|weeks?|months?|years?)\b"

    match = re.search(pattern, text)

    if match:
        return match.group(0)

    # Handle numbers like "1 month"
    if "one month" in text:
        return "1 month"

    if "two months" in text:
        return "2 months"

    if "three months" in text:
        return "3 months"

    return None


# =========================================================
# REGISTRATION ID
# =========================================================

def generate_registration_id(df):
    """
    Generates unique registration ID.
    """

    date_part = datetime.now().strftime("%Y%m%d")

    prefix = f"REG{date_part}"

    existing_ids = []

    if not df.empty and "Registration_ID" in df.columns:

        existing_ids = (
            df["Registration_ID"]
            .dropna()
            .astype(str)
            .tolist()
        )

    number = 1

    while f"{prefix}{number:03d}" in existing_ids:
        number += 1

    return f"{prefix}{number:03d}"


# =========================================================
# DUPLICATE CHECK
# =========================================================

def check_duplicate(df, email=None, phone=None):
    """
    Checks whether email or phone already exists.
    """

    if df.empty:
        return False

    if email:
        email_exists = (
            df["Email"]
            .astype(str)
            .str.lower()
            .eq(email.lower())
            .any()
        )

        if email_exists:
            return True

    if phone:
        phone_clean = re.sub(r"\D", "", str(phone))

        phone_exists = (
            df["Phone"]
            .astype(str)
            .str.replace(r"\D", "", regex=True)
            .eq(phone_clean)
            .any()
        )

        if phone_exists:
            return True

    return False


# =========================================================
# FIND REGISTRATION
# =========================================================

def find_registration(identifier):
    """
    Finds registration using:
    - Registration ID
    - Email
    - Phone
    """

    df = load_registrations()

    if df.empty:
        return None, None

    identifier = str(identifier).strip()

    # Registration ID
    matches = df[
        df["Registration_ID"]
        .astype(str)
        .str.lower()
        .eq(identifier.lower())
    ]

    if not matches.empty:
        index = matches.index[0]
        return index, df.loc[index]

    # Email
    matches = df[
        df["Email"]
        .astype(str)
        .str.lower()
        .eq(identifier.lower())
    ]

    if not matches.empty:
        index = matches.index[0]
        return index, df.loc[index]

    # Phone
    phone = re.sub(r"\D", "", identifier)

    matches = df[
        df["Phone"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)
        .eq(phone)
    ]

    if not matches.empty:
        index = matches.index[0]
        return index, df.loc[index]

    return None, None


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "AI Registration Chatbot Backend is running",
        "service": "Registration API"
    })


# =========================================================
# HEALTH API
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "backend": "online",
        "excel_file": os.path.exists(EXCEL_FILE)
    })


# =========================================================
# GET AVAILABLE DOMAINS
# =========================================================

@app.route("/api/domains", methods=["GET"])
def domains():

    return jsonify({
        "success": True,
        "domains": DOMAINS
    })


# =========================================================
# REGISTER USER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No registration data received."
            }), 400

        name = clean_name(data.get("name"))
        email = str(data.get("email", "")).strip()
        phone = str(data.get("phone", "")).strip()
        domain = str(data.get("domain", "")).strip()
        duration = str(data.get("duration", "")).strip()

        # -----------------------------
        # Name validation
        # -----------------------------

        if not name:
            return jsonify({
                "success": False,
                "message": "Please provide your name."
            }), 400

        # -----------------------------
        # Email validation
        # -----------------------------

        if not validate_email(email):
            return jsonify({
                "success": False,
                "message": "Please provide a valid email address."
            }), 400

        # -----------------------------
        # Phone validation
        # -----------------------------

        if not validate_phone(phone):
            return jsonify({
                "success": False,
                "message": "Please provide a valid 10-digit Indian mobile number."
            }), 400

        phone = re.sub(r"\D", "", phone)

        # -----------------------------
        # Domain validation
        # -----------------------------

        detected_domain = get_domain(domain)

        if detected_domain:
            domain = detected_domain

        if domain not in DOMAINS:
            return jsonify({
                "success": False,
                "message": "Please select a valid internship domain.",
                "available_domains": DOMAINS
            }), 400

        # -----------------------------
        # Duration validation
        # -----------------------------

        detected_duration = get_duration(duration)

        if detected_duration:
            duration = detected_duration

        if not duration:
            return jsonify({
                "success": False,
                "message": "Please provide internship duration."
            }), 400

        # -----------------------------
        # Load Excel
        # -----------------------------

        df = load_registrations()

        # -----------------------------
        # Duplicate check
        # -----------------------------

        if check_duplicate(df, email, phone):

            return jsonify({
                "success": False,
                "message": "A registration already exists with this email or phone number."
            }), 409

        # -----------------------------
        # Generate Registration ID
        # -----------------------------

        registration_id = generate_registration_id(df)

        # -----------------------------
        # Create registration
        # -----------------------------

        new_record = {
            "Registration_ID": registration_id,
            "Name": name,
            "Email": email,
            "Phone": phone,
            "Domain": domain,
            "Duration": duration,
            "Status": "Registered",
            "Created_At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        new_row = pd.DataFrame([new_record])

        df = pd.concat(
            [df, new_row],
            ignore_index=True
        )

        save_registrations(df)

        # -----------------------------
        # Response
        # -----------------------------

        return jsonify({
            "success": True,
            "message": "Registration completed successfully.",
            "registration": new_record
        }), 201

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Registration could not be completed.",
            "error": str(e)
        }), 500


# =========================================================
# CHECK REGISTRATION
# =========================================================

@app.route("/api/check", methods=["POST"])
def check_registration():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Please provide Registration ID, email or phone."
            }), 400

        identifier = data.get("identifier")

        if not identifier:
            return jsonify({
                "success": False,
                "message": "Please provide Registration ID, email or phone."
            }), 400

        index, record = find_registration(identifier)

        if record is None:

            return jsonify({
                "success": False,
                "message": "No registration found."
            }), 404

        registration = {
            key: (
                None if pd.isna(value)
                else str(value)
            )
            for key, value in record.to_dict().items()
        }

        return jsonify({
            "success": True,
            "message": "Registration found.",
            "registration": registration
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Could not check registration.",
            "error": str(e)
        }), 500


# =========================================================
# EDIT REGISTRATION
# =========================================================

@app.route("/api/edit", methods=["PUT"])
def edit_registration():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received."
            }), 400

        identifier = data.get("identifier")

        if not identifier:
            return jsonify({
                "success": False,
                "message": "Please provide Registration ID, email or phone."
            }), 400

        index, record = find_registration(identifier)

        if record is None:
            return jsonify({
                "success": False,
                "message": "Registration not found."
            }), 404

        df = load_registrations()

        updated = False

        # -----------------------------
        # Edit name
        # -----------------------------

        if "name" in data:

            name = clean_name(data["name"])

            if name:
                df.at[index, "Name"] = name
                updated = True

        # -----------------------------
        # Edit email
        # -----------------------------

        if "email" in data:

            email = str(data["email"]).strip()

            if not validate_email(email):

                return jsonify({
                    "success": False,
                    "message": "Invalid email address."
                }), 400

            df.at[index, "Email"] = email
            updated = True

        # -----------------------------
        # Edit phone
        # -----------------------------

        if "phone" in data:

            phone = re.sub(
                r"\D",
                "",
                str(data["phone"])
            )

            if not validate_phone(phone):

                return jsonify({
                    "success": False,
                    "message": "Invalid phone number."
                }), 400

            df.at[index, "Phone"] = phone
            updated = True

        # -----------------------------
        # Edit domain
        # -----------------------------

        if "domain" in data:

            domain = get_domain(
                str(data["domain"])
            )

            if not domain:

                return jsonify({
                    "success": False,
                    "message": "Invalid internship domain.",
                    "available_domains": DOMAINS
                }), 400

            df.at[index, "Domain"] = domain
            updated = True

        # -----------------------------
        # Edit duration
        # -----------------------------

        if "duration" in data:

            duration = get_duration(
                str(data["duration"])
            )

            if not duration:
                duration = str(
                    data["duration"]
                ).strip()

            if duration:

                df.at[index, "Duration"] = duration
                updated = True

        # -----------------------------
        # Save
        # -----------------------------

        if not updated:

            return jsonify({
                "success": False,
                "message": "No valid fields were provided for editing."
            }), 400

        save_registrations(df)

        updated_record = {
            key: (
                None if pd.isna(value)
                else str(value)
            )
            for key, value in df.loc[index].to_dict().items()
        }

        return jsonify({
            "success": True,
            "message": "Registration updated successfully.",
            "registration": updated_record
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Could not edit registration.",
            "error": str(e)
        }), 500


# =========================================================
# CANCEL REGISTRATION
# =========================================================

@app.route("/api/cancel", methods=["PUT"])
def cancel_registration():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "No data received."
            }), 400

        identifier = data.get("identifier")

        if not identifier:

            return jsonify({
                "success": False,
                "message": "Please provide Registration ID, email or phone."
            }), 400

        index, record = find_registration(identifier)

        if record is None:

            return jsonify({
                "success": False,
                "message": "Registration not found."
            }), 404

        df = load_registrations()

        df.at[index, "Status"] = "Cancelled"

        save_registrations(df)

        return jsonify({
            "success": True,
            "message": "Registration cancelled successfully.",
            "registration_id": str(
                df.at[index, "Registration_ID"]
            )
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Could not cancel registration.",
            "error": str(e)
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    initialize_excel()

    print("=" * 60)
    print("AI REGISTRATION CHATBOT BACKEND")
    print("=" * 60)
    print("Backend running at:")
    print("http://127.0.0.1:5000")
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )