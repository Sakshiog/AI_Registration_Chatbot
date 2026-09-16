import os
import uuid
from datetime import datetime

import pandas as pd
import requests

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = "ai-registration-chatbot-secret-key"


# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXCEL_FILE = os.path.join(
    BASE_DIR,
    "registrations.xlsx"
)

LOG_FILE = os.path.join(
    BASE_DIR,
    "chat_logs.csv"
)


# =========================================================
# RASA CONFIGURATION
# =========================================================

RASA_URL = "http://localhost:5005/webhooks/rest/webhook"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def load_registrations():
    """
    Load registration data from Excel.
    """

    if not os.path.exists(EXCEL_FILE):
        return pd.DataFrame()

    try:
        df = pd.read_excel(EXCEL_FILE)

        df = df.fillna("")

        return df

    except Exception as e:
        print("Excel read error:", e)
        return pd.DataFrame()


def load_logs():
    """
    Load chatbot logs from CSV.
    """

    if not os.path.exists(LOG_FILE):
        return pd.DataFrame()

    try:
        df = pd.read_csv(LOG_FILE)

        df = df.fillna("")

        return df

    except Exception as e:
        print("Log read error:", e)
        return pd.DataFrame()


# =========================================================
# CHAT PAGE
# =========================================================

@app.route("/")
def home():

    if "sender_id" not in session:
        session["sender_id"] = str(uuid.uuid4())

    return render_template("chat.html")


# =========================================================
# CHAT API
# =========================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:

        data = request.get_json()

        message = str(
            data.get("message", "")
        ).strip()

        if not message:
            return jsonify({
                "success": False,
                "message": "Please enter a message."
            }), 400


        # Create persistent sender ID
        if "sender_id" not in session:
            session["sender_id"] = str(uuid.uuid4())


        sender_id = session["sender_id"]


        # Send message to Rasa REST API
        response = requests.post(
            RASA_URL,
            json={
                "sender": sender_id,
                "message": message
            },
            timeout=60
        )


        if response.status_code != 200:

            return jsonify({
                "success": False,
                "message": (
                    "Rasa server returned an error. "
                    "Please make sure Rasa is running."
                )
            }), 500


        rasa_messages = response.json()


        bot_messages = []


        for item in rasa_messages:

            if "text" in item:

                bot_messages.append(
                    item["text"]
                )


        if not bot_messages:

            bot_messages.append(
                "I received your message, but I don't have a response yet."
            )


        return jsonify({
            "success": True,
            "messages": bot_messages
        })


    except requests.exceptions.ConnectionError:

        return jsonify({
            "success": False,
            "message": (
                "Cannot connect to Rasa. "
                "Please start the Rasa server on port 5005."
            )
        }), 503


    except requests.exceptions.Timeout:

        return jsonify({
            "success": False,
            "message": (
                "Rasa took too long to respond. "
                "Please try again."
            )
        }), 504


    except Exception as e:

        print("Chat error:", e)

        return jsonify({
            "success": False,
            "message": "Something went wrong: " + str(e)
        }), 500


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin():

    registrations = load_registrations()
    logs = load_logs()


    # -----------------------------------------------------
    # Registration statistics
    # -----------------------------------------------------

    total_registrations = len(registrations)


    today = datetime.now().strftime("%Y-%m-%d")

    today_count = 0

    if not registrations.empty:

        if "Registration_Date" in registrations.columns:

            dates = pd.to_datetime(
                registrations["Registration_Date"],
                errors="coerce"
            )

            today_count = int(
                (dates.dt.strftime("%Y-%m-%d") == today).sum()
            )


    # -----------------------------------------------------
    # Status statistics
    # -----------------------------------------------------

    status_data = {}

    if not registrations.empty and "Status" in registrations.columns:

        status_data = (
            registrations["Status"]
            .astype(str)
            .value_counts()
            .to_dict()
        )


    # -----------------------------------------------------
    # Education statistics
    # -----------------------------------------------------

    education_data = {}

    if not registrations.empty and "Education" in registrations.columns:

        education_data = (
            registrations["Education"]
            .astype(str)
            .value_counts()
            .head(10)
            .to_dict()
        )


    # -----------------------------------------------------
    # City statistics
    # -----------------------------------------------------

    city_data = {}

    if not registrations.empty and "City" in registrations.columns:

        city_data = (
            registrations["City"]
            .astype(str)
            .value_counts()
            .head(10)
            .to_dict()
        )


    # -----------------------------------------------------
    # Intent statistics
    # -----------------------------------------------------

    intent_data = {}

    if not logs.empty and "Intent" in logs.columns:

        intent_data = (
            logs["Intent"]
            .astype(str)
            .value_counts()
            .head(10)
            .to_dict()
        )

    # -----------------------------------------------------
    # Recent registrations
    # -----------------------------------------------------

    recent_registrations = []

    if not registrations.empty:

        recent_registrations = (
            registrations
            .tail(10)
            .iloc[::-1]
            .to_dict(orient="records")
        )


    # -----------------------------------------------------
    # Recent logs
    # -----------------------------------------------------

    recent_logs = []

    if not logs.empty:

        recent_logs = (
            logs
            .tail(10)
            .iloc[::-1]
            .to_dict(orient="records")
        )


    return render_template(
        "admin.html",

        total_registrations=total_registrations,

        today_count=today_count,

        status_data=status_data,

        education_data=education_data,

        city_data=city_data,

        intent_data=intent_data,

        recent_registrations=recent_registrations,

        recent_logs=recent_logs
    )


# =========================================================
# UPDATE REGISTRATION STATUS
# =========================================================

@app.route(
    "/admin/update-status",
    methods=["POST"]
)
def update_status():

    try:

        registration_id = request.form.get(
            "registration_id"
        )

        new_status = request.form.get(
            "status"
        )


        if not registration_id or not new_status:

            return redirect(
                url_for("admin")
            )


        df = load_registrations()


        if df.empty:

            return redirect(
                url_for("admin")
            )


        if "Registration_ID" not in df.columns:

            return redirect(
                url_for("admin")
            )


        mask = (
            df["Registration_ID"]
            .astype(str)
            .str.strip()
            ==
            str(registration_id).strip()
        )


        if mask.any():

            df.loc[
                mask,
                "Status"
            ] = new_status


            df.to_excel(
                EXCEL_FILE,
                index=False
            )


        return redirect(
            url_for("admin")
        )


    except Exception as e:

        print("Update status error:", e)

        return redirect(
            url_for("admin")
        )


# =========================================================
# DELETE REGISTRATION
# =========================================================

@app.route(
    "/admin/delete/<registration_id>",
    methods=["POST"]
)
def delete_registration(registration_id):

    try:

        df = load_registrations()


        if df.empty:

            return redirect(
                url_for("admin")
            )


        if "Registration_ID" not in df.columns:

            return redirect(
                url_for("admin")
            )


        df = df[
            df["Registration_ID"]
            .astype(str)
            .str.strip()
            !=
            str(registration_id).strip()
        ]


        df.to_excel(
            EXCEL_FILE,
            index=False
        )


        return redirect(
            url_for("admin")
        )


    except Exception as e:

        print("Delete error:", e)

        return redirect(
            url_for("admin")
        )


# =========================================================
# API - DASHBOARD DATA
# =========================================================

@app.route("/api/dashboard")
def dashboard_api():

    registrations = load_registrations()
    logs = load_logs()


    result = {
        "total_registrations": len(registrations),
        "total_logs": len(logs)
    }


    if not registrations.empty:

        if "Status" in registrations.columns:

            result["status"] = (
                registrations["Status"]
                .astype(str)
                .value_counts()
                .to_dict()
            )

        if "Education" in registrations.columns:

            result["education"] = (
                registrations["Education"]
                .astype(str)
                .value_counts()
                .to_dict()
            )

        if "City" in registrations.columns:

            result["cities"] = (
                registrations["City"]
                .astype(str)
                .value_counts()
                .head(10)
                .to_dict()
            )


    if not logs.empty:

        if "intent" in logs.columns:

            result["intents"] = (
                logs["intent"]
                .astype(str)
                .value_counts()
                .to_dict()
            )


    return jsonify(result)


# =========================================================
# RUN FLASK
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("AI REGISTRATION CHATBOT - FLASK WEB INTERFACE")
    print("=" * 60)
    print()
    print("Chat Interface:")
    print("http://127.0.0.1:5000")
    print()
    print("Admin Dashboard:")
    print("http://127.0.0.1:5000/admin")
    print()
    print("Make sure Rasa is running on port 5005.")
    print("=" * 60)
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )