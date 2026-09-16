import os
import re
from datetime import datetime

import pandas as pd

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction


# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCEL_FILE = os.path.join(BASE_DIR, "registrations.xlsx")
LOG_FILE = os.path.join(BASE_DIR, "chat_logs.csv")


# =========================================================
# EXCEL HELPERS
# =========================================================

COLUMNS = [
    "Registration_ID",
    "Name",
    "Email",
    "Phone",
    "Education",
    "City",
    "Domain",
    "Duration",
    "Status",
    "Created_At",
]


def initialize_excel():
    """Create registrations.xlsx if it does not exist."""

    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=COLUMNS)
        df.to_excel(EXCEL_FILE, index=False)


def load_registrations():
    """Load registrations from Excel."""

    initialize_excel()

    try:
        df = pd.read_excel(EXCEL_FILE)

        for column in COLUMNS:
            if column not in df.columns:
                df[column] = ""

        return df[COLUMNS]

    except Exception:
        return pd.DataFrame(columns=COLUMNS)


def save_registrations(df):
    """Save registrations to Excel."""

    df.to_excel(EXCEL_FILE, index=False)


# =========================================================
# LOGGING
# =========================================================

def log_message(tracker):
    """Store conversation information in chat_logs.csv."""

    try:
        user_message = tracker.latest_message.get("text", "")

        intent_data = tracker.latest_message.get("intent", {})

        intent = intent_data.get("name", "")
        confidence = intent_data.get("confidence", 0)

        row = {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "User_Message": user_message,
            "Intent": intent,
            "Confidence": confidence,
        }

        log_df = pd.DataFrame([row])

        if os.path.exists(LOG_FILE):
            log_df.to_csv(
                LOG_FILE,
                mode="a",
                header=False,
                index=False,
            )
        else:
            log_df.to_csv(
                LOG_FILE,
                mode="w",
                header=True,
                index=False,
            )

    except Exception:
        pass


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def validate_name(name):
    """Validate person's name."""

    if not name:
        return False

    name = str(name).strip()

    if len(name) < 2:
        return False

    pattern = r"^[A-Za-z][A-Za-z .'-]*$"

    return bool(re.fullmatch(pattern, name))


def validate_email(email):
    """Validate email address."""

    if not email:
        return False

    email = str(email).strip()

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return bool(re.fullmatch(pattern, email))


def validate_phone(phone):
    """Validate Indian 10-digit phone number."""

    if not phone:
        return False

    phone = re.sub(r"\D", "", str(phone))

    return bool(re.fullmatch(r"[6-9]\d{9}", phone))


def clean_text(value):
    """Clean user input."""

    if value is None:
        return ""

    return str(value).strip()


# =========================================================
# START REGISTRATION
# =========================================================

class ActionStartRegistration(Action):

    def name(self):
        return "action_start_registration"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(
            text=(
                "Sure! Let's start your registration. "
                "Please enter your full name."
            )
        )

        log_message(tracker)

        return [
            SlotSet("name", None),
            SlotSet("email", None),
            SlotSet("phone", None),
            SlotSet("education", None),
            SlotSet("city", None),
            SlotSet("status_check_mode", False),
            SlotSet("edit_mode", False),
            SlotSet("edit_registration_id", None),
            SlotSet("edit_field", None),
        ]


# =========================================================
# START EDIT REGISTRATION
# =========================================================

class ActionStartEditRegistration(Action):

    def name(self):
        return "action_start_edit_registration"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(
            text=(
                "Yes, registration details can be checked and updated. "
                "Please provide your registered email."
            )
        )

        log_message(tracker)

        return [
            SlotSet("edit_mode", True),
            SlotSet("status_check_mode", False),
            SlotSet("email", None),
            SlotSet("edit_registration_id", None),
            SlotSet("edit_field", None),
        ]


# =========================================================
# CANCEL REGISTRATION ACTIONS
# =========================================================

class ActionStartCancelRegistration(Action):

    def name(self):
        return "action_start_cancel_registration"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(
            text=(
                "I can help you cancel your registration. "
                "Please provide your registered email address."
            )
        )

        log_message(tracker)

        return [
            SlotSet("cancel_mode", True),
            SlotSet("status_check_mode", False),
            SlotSet("edit_mode", False),
            SlotSet("edit_registration_id", None),
            SlotSet("edit_field", None),
        ]


class ActionCancelRegistration(Action):

    def name(self):
        return "action_cancel_registration"

    def run(self, dispatcher, tracker, domain):

        email = tracker.get_slot("email")

        if not email:
            dispatcher.utter_message(
                text="Please provide your registered email address."
            )
            return []

        email = str(email).strip().lower()

        try:
            if not os.path.exists(EXCEL_FILE):
                dispatcher.utter_message(
                    text="Sorry, registration records could not be found."
                )
                return [
                    SlotSet("cancel_mode", False)
                ]

            df = pd.read_excel(EXCEL_FILE)

            if "Email" not in df.columns:
                dispatcher.utter_message(
                    text="Sorry, registration records are not configured correctly."
                )
                return [
                    SlotSet("cancel_mode", False)
                ]

            df["Email"] = df["Email"].astype(str).str.strip().str.lower()

            matches = df[df["Email"] == email]

            if matches.empty:
                dispatcher.utter_message(
                    text=(
                        "❌ No registration was found with this email address. "
                        "Please check your email and try again."
                    )
                )

                log_message(tracker)

                return [
                    SlotSet("cancel_mode", False)
                ]

            index = matches.index[0]

            registration_id = str(
                df.loc[index, "Registration_ID"]
            )

            current_status = str(
                df.loc[index, "Status"]
            ).strip().lower()

            if current_status == "cancelled":
                dispatcher.utter_message(
                    text=(
                        f"ℹ️ Your registration is already cancelled.\n\n"
                        f"Registration ID: {registration_id}"
                    )
                )

                log_message(tracker)

                return [
                    SlotSet("cancel_mode", False)
                ]

            df.loc[index, "Status"] = "Cancelled"

            df.to_excel(EXCEL_FILE, index=False)

            dispatcher.utter_message(
                text=(
                    "✅ Your registration has been successfully cancelled.\n\n"
                    f"Registration ID: {registration_id}\n"
                    "Status: Cancelled"
                )
            )

            log_message(tracker)

            return [
                SlotSet("cancel_mode", False),
                SlotSet("email", None),
                SlotSet("name", None),
                SlotSet("phone", None),
                SlotSet("education", None),
                SlotSet("city", None),
            ]

        except Exception as e:

            print(f"Cancellation error: {e}")

            dispatcher.utter_message(
                text=(
                    "❌ Sorry, I could not cancel the registration "
                    "because of a system error."
                )
            )

            log_message(tracker)

            return [
                SlotSet("cancel_mode", False)
            ]

# =========================================================
# CANCEL REGISTRATION
# =========================================================

class ActionStartCancelRegistration(Action):

    def name(self):
        return "action_start_cancel_registration"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(
            text=(
                "I can help you cancel your registration. "
                "Please provide your registered email address."
            )
        )

        log_message(tracker)

        return [
            SlotSet("cancel_mode", True),
            SlotSet("status_check_mode", False),
            SlotSet("edit_mode", False),
            SlotSet("edit_registration_id", None),
            SlotSet("edit_field", None),
        ]


class ActionCancelRegistration(Action):

    def name(self):
        return "action_cancel_registration"

    def run(self, dispatcher, tracker, domain):

        email = tracker.get_slot("email")

        if not email:
            dispatcher.utter_message(
                text="Please provide your registered email address."
            )
            return []

        email = str(email).strip().lower()

        try:

            if not os.path.exists(EXCEL_FILE):
                dispatcher.utter_message(
                    text="Sorry, registration records could not be found."
                )
                return [SlotSet("cancel_mode", False)]

            df = pd.read_excel(EXCEL_FILE)

            if "Email" not in df.columns:
                dispatcher.utter_message(
                    text="Sorry, registration records are not configured correctly."
                )
                return [SlotSet("cancel_mode", False)]

            df["Email"] = (
                df["Email"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            matches = df[df["Email"] == email]

            if matches.empty:
                dispatcher.utter_message(
                    text=(
                        "❌ No registration was found with this email address. "
                        "Please check your email and try again."
                    )
                )

                log_message(tracker)

                return [
                    SlotSet("cancel_mode", False)
                ]

            index = matches.index[0]

            registration_id = str(
                df.loc[index, "Registration_ID"]
            )

            current_status = str(
                df.loc[index, "Status"]
            ).strip().lower()

            if current_status == "cancelled":

                dispatcher.utter_message(
                    text=(
                        "ℹ️ Your registration is already cancelled.\n\n"
                        f"Registration ID: {registration_id}"
                    )
                )

                log_message(tracker)

                return [
                    SlotSet("cancel_mode", False)
                ]

            df.loc[index, "Status"] = "Cancelled"

            df.to_excel(
                EXCEL_FILE,
                index=False
            )

            dispatcher.utter_message(
                text=(
                    "✅ Your registration has been successfully cancelled.\n\n"
                    f"Registration ID: {registration_id}\n"
                    "Status: Cancelled"
                )
            )

            log_message(tracker)

            return [
                SlotSet("cancel_mode", False),
                SlotSet("email", None),
                SlotSet("name", None),
                SlotSet("phone", None),
                SlotSet("education", None),
                SlotSet("city", None),
            ]

        except Exception as e:

            print(f"Cancellation error: {e}")

            dispatcher.utter_message(
                text=(
                    "❌ Sorry, I could not cancel the registration "
                    "because of a system error."
                )
            )

            log_message(tracker)

            return [
                SlotSet("cancel_mode", False)
            ]




# =========================================================
# VALIDATE REGISTRATION
# =========================================================

class ActionValidateRegistration(Action):

    def name(self):
        return "action_validate_registration"

    def run(self, dispatcher, tracker, domain):

        user_text = clean_text(
            tracker.latest_message.get("text", "")
        )


        # -------------------------------------------------
        # CANCEL MODE - EMAIL
        # -------------------------------------------------

        if (
            tracker.get_slot("cancel_mode")
            and validate_email(user_text)
        ):
            return [
                SlotSet("email", user_text),
                FollowupAction("action_cancel_registration"),
            ]

        # -------------------------------------------------
        # EDIT MODE - EMAIL
        # -------------------------------------------------

        if (
            tracker.get_slot("edit_mode")
            and not tracker.get_slot("edit_registration_id")
            and validate_email(user_text)
        ):

            return [
                SlotSet("email", user_text),
                FollowupAction("action_edit_registration"),
            ]

        # -------------------------------------------------
        # EDIT MODE - FIELD SELECTION
        # -------------------------------------------------

        if (
            tracker.get_slot("edit_mode")
            and tracker.get_slot("edit_registration_id")
            and not tracker.get_slot("edit_field")
        ):

            text_lower = user_text.lower()

            field = None

            if (
                "name" in text_lower
                or "naam" in text_lower
            ):
                field = "Name"

            elif (
                "phone" in text_lower
                or "mobile" in text_lower
                or "number" in text_lower
            ):
                field = "Phone"

            elif (
                "education" in text_lower
                or "qualification" in text_lower
                or "degree" in text_lower
            ):
                field = "Education"

            elif (
                "city" in text_lower
                or "location" in text_lower
                or "shehar" in text_lower
            ):
                field = "City"

            if field:

                dispatcher.utter_message(
                    text=(
                        f"Okay. You want to update your "
                        f"{field.lower()}. "
                        f"Please enter the new value."
                    )
                )

                return [
                    SlotSet("edit_field", field)
                ]

        # -------------------------------------------------
        # EDIT MODE - NEW VALUE
        # -------------------------------------------------

        if (
            tracker.get_slot("edit_mode")
            and tracker.get_slot("edit_registration_id")
            and tracker.get_slot("edit_field")
        ):

            return [
                FollowupAction("action_edit_registration")
            ]

        # -------------------------------------------------
        # STATUS CHECK MODE
        # -------------------------------------------------

        if tracker.get_slot("status_check_mode"):

            if validate_email(user_text):

                return [
                    SlotSet("email", user_text),
                    FollowupAction("action_check_registration"),
                ]

            dispatcher.utter_message(
                text="Please provide a valid email address."
            )

            return []

        # -------------------------------------------------
        # NORMAL REGISTRATION - NAME
        # -------------------------------------------------

        if tracker.get_slot("name") is None:

            if validate_name(user_text):

                return [
                    SlotSet("name", user_text),
                    FollowupAction("utter_ask_email"),
                ]

            dispatcher.utter_message(
                text=(
                    "Please enter a valid full name. "
                    "Use letters and spaces only."
                )
            )

            return []

        # -------------------------------------------------
        # NORMAL REGISTRATION - EMAIL
        # -------------------------------------------------

        if tracker.get_slot("email") is None:

            if not validate_email(user_text):

                dispatcher.utter_message(
                    text="Please enter a valid email address."
                )

                return []

            df = load_registrations()

            if not df.empty and "Email" in df.columns:

                existing_emails = (
                    df["Email"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                )

                if user_text.lower() in existing_emails.values:

                    dispatcher.utter_message(
                        text=(
                            "⚠️ This email is already registered. "
                            "Please use another email address."
                        )
                    )

                    return []

            return [
                SlotSet("email", user_text),
                FollowupAction("utter_ask_phone"),
            ]

        # -------------------------------------------------
        # NORMAL REGISTRATION - PHONE
        # -------------------------------------------------

        if tracker.get_slot("phone") is None:

            phone = re.sub(r"\D", "", user_text)

            if not validate_phone(phone):

                dispatcher.utter_message(
                    text=(
                        "Please enter a valid 10-digit mobile number "
                        "starting with 6, 7, 8, or 9."
                    )
                )

                return []

            df = load_registrations()

            if not df.empty and "Phone" in df.columns:

                existing_phones = (
                    df["Phone"]
                    .astype(str)
                    .str.replace(r"\D", "", regex=True)
                )

                if phone in existing_phones.values:

                    dispatcher.utter_message(
                        text=(
                            "⚠️ This phone number is already registered. "
                            "Please use another number."
                        )
                    )

                    return []

            return [
                SlotSet("phone", phone),
                FollowupAction("utter_ask_education"),
            ]

        # -------------------------------------------------
        # NORMAL REGISTRATION - EDUCATION
        # -------------------------------------------------

        if tracker.get_slot("education") is None:

            if len(user_text) < 2:

                dispatcher.utter_message(
                    text="Please enter your educational qualification."
                )

                return []

            return [
                SlotSet("education", user_text),
                FollowupAction("utter_ask_city"),
            ]

        # -------------------------------------------------
        # NORMAL REGISTRATION - CITY
        # -------------------------------------------------

        if tracker.get_slot("city") is None:

            if len(user_text) < 2:

                dispatcher.utter_message(
                    text="Please enter your city."
                )

                return []

            return [
                SlotSet("city", user_text),
                FollowupAction("action_save_registration"),
            ]

        return []


# =========================================================
# SAVE REGISTRATION
# =========================================================

class ActionSaveRegistration(Action):

    def name(self):
        return "action_save_registration"

    def run(self, dispatcher, tracker, domain):

        try:

            df = load_registrations()

            name = clean_text(tracker.get_slot("name"))
            email = clean_text(tracker.get_slot("email"))
            phone = clean_text(tracker.get_slot("phone"))
            education = clean_text(tracker.get_slot("education"))
            city = clean_text(tracker.get_slot("city"))

            # ---------------------------------------------
            # FINAL VALIDATION
            # ---------------------------------------------

            if not validate_name(name):

                dispatcher.utter_message(
                    text="Registration failed: invalid name."
                )

                return []

            if not validate_email(email):

                dispatcher.utter_message(
                    text="Registration failed: invalid email."
                )

                return []

            if not validate_phone(phone):

                dispatcher.utter_message(
                    text="Registration failed: invalid phone number."
                )

                return []

            # ---------------------------------------------
            # DUPLICATE CHECK
            # ---------------------------------------------

            if not df.empty:

                if "Email" in df.columns:

                    emails = (
                        df["Email"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )

                    if email.lower() in emails.values:

                        dispatcher.utter_message(
                            text=(
                                "⚠️ This email is already registered."
                            )
                        )

                        return []

                if "Phone" in df.columns:

                    phones = (
                        df["Phone"]
                        .astype(str)
                        .str.replace(r"\D", "", regex=True)
                    )

                    if phone in phones.values:

                        dispatcher.utter_message(
                            text=(
                                "⚠️ This phone number is already registered."
                            )
                        )

                        return []

            # ---------------------------------------------
            # REGISTRATION ID
            # ---------------------------------------------

            today = datetime.now().strftime("%Y%m%d")

            count_today = 0

            if not df.empty and "Registration_ID" in df.columns:

                prefix = f"REG{today}"

                count_today = sum(
                    str(value).startswith(prefix)
                    for value in df["Registration_ID"]
                )

            registration_id = (
                f"REG{today}{count_today + 1:03d}"
            )

            # ---------------------------------------------
            # NEW RECORD
            # ---------------------------------------------

            new_record = {
                "Registration_ID": registration_id,
                "Name": name,
                "Email": email,
                "Phone": phone,
                "Education": education,
                "City": city,
                "Domain": "",
                "Duration": "",
                "Status": "Registered",
                "Created_At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            df = pd.concat(
                [
                    df,
                    pd.DataFrame([new_record]),
                ],
                ignore_index=True,
            )

            save_registrations(df)

            dispatcher.utter_message(
                text=(
                    "🎉 Registration completed successfully!\n\n"
                    f"Registration ID: {registration_id}\n"
                    f"Name: {name}\n"
                    f"Email: {email}\n"
                    f"Phone: {phone}\n"
                    f"Education: {education}\n"
                    f"City: {city}\n\n"
                    "Your details have been saved successfully."
                )
            )

            log_message(tracker)

            return [
                SlotSet("status_check_mode", False),
                SlotSet("edit_mode", False),
                SlotSet("edit_registration_id", None),
                SlotSet("edit_field", None),
            ]

        except Exception as error:

            dispatcher.utter_message(
                text=(
                    "Sorry, there was a problem while saving "
                    "your registration."
                )
            )

            print("SAVE REGISTRATION ERROR:", error)

            return []


# =========================================================
# CHECK REGISTRATION
# =========================================================

class ActionCheckRegistration(Action):

    def name(self):
        return "action_check_registration"

    def run(self, dispatcher, tracker, domain):

        email = clean_text(
            tracker.get_slot("email")
        )

        if not validate_email(email):

            dispatcher.utter_message(
                text="Please provide the email used during registration."
            )

            return [
                SlotSet("status_check_mode", True)
            ]

        df = load_registrations()

        if df.empty:

            dispatcher.utter_message(
                text="No registrations are currently available."
            )

            return [
                SlotSet("status_check_mode", False)
            ]

        matches = df[
            df["Email"]
            .astype(str)
            .str.strip()
            .str.lower()
            == email.lower()
        ]

        if matches.empty:

            dispatcher.utter_message(
                text=(
                    "❌ No registration was found with this email address."
                )
            )

            return [
                SlotSet("status_check_mode", False)
            ]

        row = matches.iloc[0]

        dispatcher.utter_message(
            text=(
                "✅ Registration found!\n\n"
                f"Registration ID: {row['Registration_ID']}\n"
                f"Name: {row['Name']}\n"
                f"Email: {row['Email']}\n"
                f"Status: {row['Status']}"
            )
        )

        log_message(tracker)

        return [
            SlotSet("status_check_mode", False)
        ]


# =========================================================
# EDIT REGISTRATION
# =========================================================

class ActionEditRegistration(Action):

    def name(self):
        return "action_edit_registration"

    def run(self, dispatcher, tracker, domain):

        try:

            email = clean_text(
                tracker.get_slot("email")
            )

            edit_field = tracker.get_slot("edit_field")
            edit_registration_id = tracker.get_slot(
                "edit_registration_id"
            )

            df = load_registrations()

            if df.empty:

                dispatcher.utter_message(
                    text="No registrations were found."
                )

                return []

            # ---------------------------------------------
            # FIND REGISTRATION
            # ---------------------------------------------

            if not edit_registration_id:

                if not validate_email(email):

                    dispatcher.utter_message(
                        text="Please provide a valid registered email."
                    )

                    return []

                matches = df[
                    df["Email"]
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    == email.lower()
                ]

                if matches.empty:

                    dispatcher.utter_message(
                        text=(
                            "❌ No registration was found with "
                            "this email address."
                        )
                    )

                    return [
                        SlotSet("edit_mode", True),
                        SlotSet("edit_registration_id", None),
                        SlotSet("edit_field", None),
                    ]

                row_index = matches.index[0]
                registration_id = str(
                    df.loc[row_index, "Registration_ID"]
                )

                dispatcher.utter_message(
                    text=(
                        "✅ Registration found!\n\n"
                        f"Registration ID: {registration_id}\n"
                        f"Name: {df.loc[row_index, 'Name']}\n"
                        f"Email: {df.loc[row_index, 'Email']}\n\n"
                        "What would you like to update?\n"
                        "• Name\n"
                        "• Phone\n"
                        "• Education\n"
                        "• City"
                    )
                )

                return [
                    SlotSet(
                        "edit_registration_id",
                        registration_id,
                    )
                ]

            # ---------------------------------------------
            # FIND ROW USING REGISTRATION ID
            # ---------------------------------------------

            matches = df[
                df["Registration_ID"]
                .astype(str)
                == str(edit_registration_id)
            ]

            if matches.empty:

                dispatcher.utter_message(
                    text="Registration record could not be found."
                )

                return [
                    SlotSet("edit_registration_id", None),
                    SlotSet("edit_field", None),
                ]

            row_index = matches.index[0]

            # ---------------------------------------------
            # FIELD NOT SELECTED
            # ---------------------------------------------

            if not edit_field:

                dispatcher.utter_message(
                    text=(
                        "What would you like to update?\n"
                        "• Name\n"
                        "• Phone\n"
                        "• Education\n"
                        "• City"
                    )
                )

                return []

            # ---------------------------------------------
            # NEW VALUE
            # ---------------------------------------------

            user_text = clean_text(
                tracker.latest_message.get("text", "")
            )

            # ---------------------------------------------
            # UPDATE NAME
            # ---------------------------------------------

            if edit_field == "Name":

                if not validate_name(user_text):

                    dispatcher.utter_message(
                        text="Please enter a valid name."
                    )

                    return []

                df.loc[row_index, "Name"] = user_text

            # ---------------------------------------------
            # UPDATE PHONE
            # ---------------------------------------------

            elif edit_field == "Phone":

                phone = re.sub(r"\D", "", user_text)

                if not validate_phone(phone):

                    dispatcher.utter_message(
                        text=(
                            "Please enter a valid 10-digit "
                            "mobile number."
                        )
                    )

                    return []

                other_rows = df.index != row_index

                existing_phones = (
                    df.loc[other_rows, "Phone"]
                    .astype(str)
                    .str.replace(r"\D", "", regex=True)
                )

                if phone in existing_phones.values:

                    dispatcher.utter_message(
                        text=(
                            "⚠️ This phone number is already "
                            "registered."
                        )
                    )

                    return []

                df.loc[row_index, "Phone"] = phone

            # ---------------------------------------------
            # UPDATE EDUCATION
            # ---------------------------------------------

            elif edit_field == "Education":

                if len(user_text) < 2:

                    dispatcher.utter_message(
                        text="Please enter a valid qualification."
                    )

                    return []

                df.loc[row_index, "Education"] = user_text

            # ---------------------------------------------
            # UPDATE CITY
            # ---------------------------------------------

            elif edit_field == "City":

                if len(user_text) < 2:

                    dispatcher.utter_message(
                        text="Please enter a valid city."
                    )

                    return []

                df.loc[row_index, "City"] = user_text

            else:

                dispatcher.utter_message(
                    text="Sorry, that field cannot be edited."
                )

                return []

            # ---------------------------------------------
            # SAVE
            # ---------------------------------------------

            save_registrations(df)

            dispatcher.utter_message(
                text=(
                    "✅ Your registration has been updated "
                    "successfully!"
                )
            )

            log_message(tracker)

            return [
                SlotSet("edit_mode", False),
                SlotSet("edit_registration_id", None),
                SlotSet("edit_field", None),
            ]

        except Exception as error:

            dispatcher.utter_message(
                text=(
                    "Sorry, there was a problem while "
                    "updating your registration."
                )
            )

            print("EDIT REGISTRATION ERROR:", error)

            return []


# =========================================================
# FAQ
# =========================================================

class ActionHandleFAQ(Action):

    def name(self):
        return "action_handle_faq"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(
            text=(
                "I can help you with:\n"
                "• Registration process\n"
                "• Required information\n"
                "• Registration status\n"
                "• Editing registration details\n"
                "• Internship domains\n"
                "• General registration questions"
            )
        )

        log_message(tracker)

        return []


# =========================================================
# GEMINI FALLBACK
# =========================================================

class ActionGeminiFallback(Action):

    def name(self):
        return "action_gemini_fallback"

    def run(self, dispatcher, tracker, domain):

        user_text = clean_text(
            tracker.latest_message.get("text", "")
        )

        try:

            import os

            api_key = os.getenv("GEMINI_API_KEY")

            if not api_key:

                dispatcher.utter_message(
                    text=(
                        "I'm sorry, I couldn't understand that. "
                        "Please ask me about registration, status, "
                        "editing, or FAQs."
                    )
                )

                return []

            from google import genai

            client = genai.Client(
                api_key=api_key
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    "You are an internship registration assistant. "
                    "Answer briefly and helpfully. "
                    "Do not invent registration fees, dates, "
                    "companies, policies, or official information.\n\n"
                    f"User: {user_text}"
                ),
            )

            answer = getattr(
                response,
                "text",
                None,
            )

            if answer:

                dispatcher.utter_message(
                    text=answer
                )

            else:

                dispatcher.utter_message(
                    text=(
                        "I'm sorry, I couldn't generate a response "
                        "right now."
                    )
                )

        except Exception as error:

            print("GEMINI ERROR:", error)

            dispatcher.utter_message(
                text=(
                    "I'm sorry, I couldn't understand that. "
                    "Please ask me about the registration process."
                )
            )

        log_message(tracker)

        return []


# =========================================================
# CONVERSATION LOGGING
# =========================================================

class ActionLogConversation(Action):

    def name(self):
        return "action_log_conversation"

    def run(self, dispatcher, tracker, domain):

        log_message(tracker)

        return []