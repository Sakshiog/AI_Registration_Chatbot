import os
import re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from google import genai

from intent_model import IntentClassifier


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if API_KEY:
    client = genai.Client(api_key=API_KEY)
else:
    client = None

MODEL_NAME = "gemini-3.6-flash"

# IMPORTANT:
# Backend must be running at this address.
BACKEND_URL = "http://127.0.0.1:5000"

EXCEL_FILE = "registrations.xlsx"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Registration Assistant",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# DOMAINS
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
    "Android Development",
]


# =========================================================
# REQUIRED EXCEL COLUMNS
# =========================================================

REQUIRED_COLUMNS = [
    "Registration_ID",
    "Name",
    "Email",
    "Phone",
    "Domain",
    "Duration",
    "Status",
    "Created_At",
]


# =========================================================
# CLASSIFIER
# =========================================================

@st.cache_resource
def load_classifier():
    try:
        return IntentClassifier("intents.json")
    except Exception:
        return None


classifier = load_classifier()


# =========================================================
# EXCEL FUNCTIONS
# =========================================================

def initialize_excel():

    if not os.path.exists(EXCEL_FILE):

        df = pd.DataFrame(
            columns=REQUIRED_COLUMNS
        )

        df.to_excel(
            EXCEL_FILE,
            index=False
        )


def load_registrations():

    initialize_excel()

    try:

        df = pd.read_excel(EXCEL_FILE)

        for column in REQUIRED_COLUMNS:

            if column not in df.columns:
                df[column] = ""

        return df[REQUIRED_COLUMNS]

    except Exception:

        return pd.DataFrame(
            columns=REQUIRED_COLUMNS
        )


def save_registrations(df):

    df.to_excel(
        EXCEL_FILE,
        index=False
    )


# =========================================================
# BACKEND FUNCTIONS
# =========================================================

def backend_health():

    try:

        response = requests.get(
            f"{BACKEND_URL}/api/health",
            timeout=5
        )

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Backend is not running."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


def backend_register(data):

    try:

        response = requests.post(
            f"{BACKEND_URL}/api/register",
            json=data,
            timeout=10
        )

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Backend is not running."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


def backend_check(identifier):

    try:

        response = requests.post(
            f"{BACKEND_URL}/api/check",
            json={
                "identifier": identifier
            },
            timeout=10
        )

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Backend is not running."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


def backend_edit(identifier, updates):

    try:

        data = {
            "identifier": identifier,
            **updates
        }

        response = requests.put(
            f"{BACKEND_URL}/api/edit",
            json=data,
            timeout=10
        )

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Backend is not running."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


def backend_cancel(identifier):

    try:

        response = requests.put(
            f"{BACKEND_URL}/api/cancel",
            json={
                "identifier": identifier
            },
            timeout=10
        )

        return response.json()

    except requests.exceptions.ConnectionError:

        return {
            "success": False,
            "message": "Backend is not running."
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def validate_email(email):

    if not email:
        return False

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return bool(
        re.fullmatch(
            pattern,
            email.strip()
        )
    )


def validate_phone(phone):

    if not phone:
        return False

    phone = re.sub(
        r"\D",
        "",
        str(phone)
    )

    return bool(
        re.fullmatch(
            r"[6-9]\d{9}",
            phone
        )
    )


def clean_name(name):

    if not name:
        return ""

    name = re.sub(
        r"\s+",
        " ",
        str(name).strip()
    )

    return name


# =========================================================
# DOMAIN EXTRACTION
# =========================================================

def get_domain(text):

    if not text:
        return None

    text_lower = text.lower()

    sorted_domains = sorted(
        DOMAINS,
        key=len,
        reverse=True
    )

    for domain in sorted_domains:

        if domain.lower() in text_lower:
            return domain

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
        "python development": "Python Development",

        "web": "Web Development",
        "web development": "Web Development",

        "full stack": "Full Stack Development",
        "fullstack": "Full Stack Development",

        "java": "Java Development",
        "java development": "Java Development",

        "cloud": "Cloud Computing",
        "cloud computing": "Cloud Computing",

        "cyber": "Cyber Security",
        "cyber security": "Cyber Security",

        "android": "Android Development",
        "android development": "Android Development",
    }

    for alias, domain in aliases.items():

        if re.search(
            rf"\b{re.escape(alias)}\b",
            text_lower
        ):
            return domain

    return None


# =========================================================
# DURATION EXTRACTION
# =========================================================

def get_duration(text):

    if not text:
        return None

    text_lower = text.lower().strip()

    patterns = [

        r"\b\d+\s*days?\b",

        r"\b\d+\s*weeks?\b",

        r"\b\d+\s*months?\b",

        r"\b\d+\s*years?\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text_lower
        )

        if match:

            return match.group(0)

    return None


# =========================================================
# REGISTRATION ID
# =========================================================

def generate_registration_id(df):

    today = datetime.now().strftime("%Y%m%d")

    prefix = f"REG{today}"

    count = 0

    if (
        not df.empty
        and "Registration_ID" in df.columns
    ):

        for registration_id in df[
            "Registration_ID"
        ].astype(str):

            if registration_id.startswith(prefix):

                count += 1

    return f"{prefix}{count + 1:03d}"


# =========================================================
# LOCAL FIND FUNCTION
# =========================================================

def find_registration(identifier):

    df = load_registrations()

    if df.empty:
        return None, None

    identifier = str(
        identifier
    ).strip()

    # Registration ID
    matches = df[
        df["Registration_ID"]
        .astype(str)
        .str.strip()
        .str.lower()
        == identifier.lower()
    ]

    if not matches.empty:

        index = matches.index[0]

        return index, df.loc[index]

    # Email
    matches = df[
        df["Email"]
        .astype(str)
        .str.strip()
        .str.lower()
        == identifier.lower()
    ]

    if not matches.empty:

        index = matches.index[0]

        return index, df.loc[index]

    # Phone
    clean_identifier = re.sub(
        r"\D",
        "",
        identifier
    )

    matches = df[
        df["Phone"]
        .astype(str)
        .str.replace(
            r"\D",
            "",
            regex=True
        )
        == clean_identifier
    ]

    if not matches.empty:

        index = matches.index[0]

        return index, df.loc[index]

    return None, None


# =========================================================
# DUPLICATE CHECK
# =========================================================

def check_duplicate(email, phone):

    df = load_registrations()

    if df.empty:
        return False

    email = str(
        email
    ).strip().lower()

    phone = re.sub(
        r"\D",
        "",
        str(phone)
    )

    email_exists = (
        df["Email"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq(email)
        .any()
    )

    phone_exists = (
        df["Phone"]
        .astype(str)
        .str.replace(
            r"\D",
            "",
            regex=True
        )
        .eq(phone)
        .any()
    )

    return email_exists or phone_exists


# =========================================================
# GEMINI AI
# =========================================================

def ask_ai(user_message):

    if not client:

        return (
            "⚠️ **Gemini AI is not connected.**\n\n"
            "Please check your `GEMINI_API_KEY` "
            "in the `.env` file."
        )

    prompt = f"""
You are an AI Registration Assistant for an internship program.

User message:
{user_message}

Give a short, friendly and helpful response.

The assistant handles:

- Internship registration
- Registration status
- Editing registration
- Cancellation
- Eligibility
- Internship information
- Internship domains
- General internship-related questions

Important rules:

- Do not start registration unless the user clearly asks to register or apply.
- Do not invent internship fees.
- Do not invent dates.
- Do not invent companies.
- Do not invent policies.
- If exact information is unavailable, clearly say that it is not available.
"""

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:

            return response.text.strip()

        return "⚠️ Gemini returned an empty response."

    except Exception as e:

        return (
            "❌ **Gemini AI Error**\n\n"
            f"`{type(e).__name__}: {str(e)}`\n\n"
            "Please check your Gemini API key, "
            "SDK installation, model name, "
            "API quota, or internet connection."
        )


# =========================================================
# INTENT CLASSIFICATION
# =========================================================

def classify_intent(text):

    text_lower = text.lower().strip()

    # -----------------------------
    # Greeting
    # -----------------------------

    greeting_words = [
        "hi",
        "hello",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
    ]

    if text_lower in greeting_words:

        return "GREETING"

    # -----------------------------
    # Thank You
    # -----------------------------

    thank_words = [
        "thank you",
        "thanks",
        "thankyou",
        "thx",
    ]

    if text_lower in thank_words:

        return "THANK_YOU"

    # -----------------------------
    # Help
    # -----------------------------

    if text_lower in [
        "help",
        "what can you do",
        "what can you help me with",
    ]:

        return "HELP"

    # -----------------------------
    # Cancel
    # -----------------------------

    cancel_words = [
        "cancel registration",
        "cancel my registration",
        "cancel application",
        "cancel my application",
    ]

    if any(
        phrase in text_lower
        for phrase in cancel_words
    ):

        return "CANCEL"

    # -----------------------------
    # Check status
    # -----------------------------

    check_words = [
        "check status",
        "registration status",
        "application status",
        "check my registration",
        "check registration",
        "status",
    ]

    if any(
        phrase in text_lower
        for phrase in check_words
    ):

        return "CHECK"

    # -----------------------------
    # Edit
    # -----------------------------

    edit_words = [
        "edit registration",
        "edit my registration",
        "change registration",
        "update registration",
        "edit application",
        "update application",
    ]

    if any(
        phrase in text_lower
        for phrase in edit_words
    ):

        return "EDIT"

    # -----------------------------
    # Eligibility
    # -----------------------------

    eligibility_words = [
        "eligibility",
        "eligible",
        "who can apply",
        "am i eligible",
        "can i apply",
    ]

    if any(
        phrase in text_lower
        for phrase in eligibility_words
    ):

        return "ELIGIBILITY"

    # -----------------------------
    # Registration
    # -----------------------------

    register_words = [
        "register",
        "registration",
        "apply",
        "application",
        "enroll",
        "enrollment",
        "join internship",
        "want to register",
        "i want to apply",
        "i want to register",
    ]

    if any(
        phrase in text_lower
        for phrase in register_words
    ):

        return "REGISTER"

    # -----------------------------
    # Try ML classifier
    # -----------------------------

    if classifier:

        try:

            if hasattr(classifier, "predict"):

                result = classifier.predict(text)

                if isinstance(result, str):

                    return result.upper()

            if hasattr(classifier, "classify"):

                result = classifier.classify(text)

                if isinstance(result, str):

                    return result.upper()

        except Exception:

            pass

    return "GENERAL"


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = []


if "mode" not in st.session_state:

    st.session_state.mode = None


if "registration" not in st.session_state:

    st.session_state.registration = {

        "name": "",
        "email": "",
        "phone": "",
        "domain": "",
        "duration": "",
    }


if "edit_data" not in st.session_state:

    st.session_state.edit_data = {}


# =========================================================
# CHAT FUNCTIONS
# =========================================================

def add_bot_message(message):

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": message,
        }
    )


def add_user_message(message):

    st.session_state.messages.append(
        {
            "role": "user",
            "content": message,
        }
    )


def reset_registration():

    st.session_state.registration = {

        "name": "",
        "email": "",
        "phone": "",
        "domain": "",
        "duration": "",
    }


def start_registration():

    reset_registration()

    st.session_state.mode = "REGISTER"

    add_bot_message(
        "Sure! 😊 Let's start your internship registration.\n\n"
        "Please enter your **full name**."
    )


def reset_chat():

    st.session_state.messages = []

    st.session_state.mode = None

    reset_registration()

    st.session_state.edit_data = {}


# =========================================================
# HEADER
# =========================================================

st.title("🤖 AI Registration Assistant")

st.write(
    "Register, check status, edit or cancel your internship registration."
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Assistant")

    backend_status = backend_health()

    if backend_status.get("success"):

        st.success("Backend Connected")

    else:

        st.error("Backend Offline")

    st.divider()

    st.subheader("Available Domains")

    for domain in DOMAINS:

        st.write(f"• {domain}")

    st.divider()

    if st.button(
        "🆕 New Chat",
        use_container_width=True
    ):

        reset_chat()

        st.rerun()


# =========================================================
# INITIAL MESSAGE
# =========================================================

if not st.session_state.messages:

    add_bot_message(
        "👋 **Hello! I'm your AI Registration Assistant.**\n\n"
        "I can help you with:\n\n"
        "• Internship registration\n"
        "• Check registration status\n"
        "• Edit registration\n"
        "• Cancel registration\n"
        "• Eligibility information\n"
        "• Internship domains\n\n"
        "You can type **register** to start."
    )


# =========================================================
# DISPLAY CHAT
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# USER INPUT
# =========================================================

user_input = st.chat_input(
    "Type your message..."
)


# =========================================================
# MAIN CHAT PROCESSING
# =========================================================

if user_input:

    user_input = user_input.strip()

    if not user_input:

        st.stop()

    text_lower = user_input.lower()

    add_user_message(user_input)


    # =====================================================
    # EXIT
    # =====================================================

    if text_lower in [
        "exit",
        "quit",
        "bye",
    ]:

        add_bot_message(
            "Goodbye! 👋\n\n"
            "You can come back anytime."
        )

        st.rerun()


    # =====================================================
    # ACTIVE REGISTRATION FLOW
    # =====================================================

    if st.session_state.mode == "REGISTER":

        registration = st.session_state.registration


        # -------------------------------------------------
        # NAME
        # -------------------------------------------------

        if not registration["name"]:

            name = clean_name(
                user_input
            )

            if len(name) < 2:

                add_bot_message(
                    "Please enter a valid full name."
                )

            else:

                registration["name"] = name

                add_bot_message(
                    f"Nice to meet you, **{name}**! 😊\n\n"
                    "Please enter your **email address**."
                )

            st.rerun()


        # -------------------------------------------------
        # EMAIL
        # -------------------------------------------------

        if not registration["email"]:

            email_match = re.search(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                user_input
            )

            if not email_match:

                add_bot_message(
                    "Please enter a valid email address.\n\n"
                    "Example: `sakshi@gmail.com`"
                )

            else:

                email = email_match.group(0).strip()

                if not validate_email(email):

                    add_bot_message(
                        "That email address doesn't look valid. "
                        "Please enter a valid email."
                    )

                else:

                    registration["email"] = email

                    add_bot_message(
                        "Great! 👍\n\n"
                        "Now please enter your **10-digit mobile number**."
                    )

            st.rerun()


        # -------------------------------------------------
        # PHONE
        # -------------------------------------------------

        if not registration["phone"]:

            phone = re.sub(
                r"\D",
                "",
                user_input
            )

            if not validate_phone(phone):

                add_bot_message(
                    "Please enter a valid 10-digit Indian mobile number "
                    "starting with 6, 7, 8 or 9."
                )

            else:

                registration["phone"] = phone

                domain_list = "\n".join(
                    [
                        f"• {domain}"
                        for domain in DOMAINS
                    ]
                )

                add_bot_message(
                    "Perfect! 📱\n\n"
                    "Please choose your **internship domain**.\n\n"
                    f"{domain_list}"
                )

            st.rerun()


        # -------------------------------------------------
        # DOMAIN
        # -------------------------------------------------

        if not registration["domain"]:

            domain = get_domain(
                user_input
            )

            if not domain:

                add_bot_message(
                    "Please enter one of the available domains:\n\n"
                    + "\n".join(
                        [
                            f"• {domain}"
                            for domain in DOMAINS
                        ]
                    )
                )

            else:

                registration["domain"] = domain

                add_bot_message(
                    f"Great choice! 🎯\n\n"
                    f"Selected domain: **{domain}**\n\n"
                    "Now enter your internship **duration**.\n\n"
                    "Example: `1 month`, `2 months`, `4 weeks`."
                )

            st.rerun()


        # -------------------------------------------------
        # DURATION
        # -------------------------------------------------

        if not registration["duration"]:

            duration = get_duration(
                user_input
            )

            if not duration:

                add_bot_message(
                    "Please enter a valid duration.\n\n"
                    "Examples:\n"
                    "• 1 month\n"
                    "• 2 months\n"
                    "• 4 weeks\n"
                    "• 30 days"
                )

            else:

                registration["duration"] = duration

                add_bot_message(
                    "Please review your registration details:\n\n"
                    f"👤 **Name:** {registration['name']}\n\n"
                    f"📧 **Email:** {registration['email']}\n\n"
                    f"📱 **Phone:** {registration['phone']}\n\n"
                    f"🎯 **Domain:** {registration['domain']}\n\n"
                    f"⏱️ **Duration:** {registration['duration']}\n\n"
                    "Do you want to **confirm** this registration?\n\n"
                    "Type **Yes** to confirm or **No** to cancel."
                )

                st.session_state.mode = "REGISTER_CONFIRM"

            st.rerun()


    # =====================================================
    # REGISTRATION CONFIRMATION
    # =====================================================

    if st.session_state.mode == "REGISTER_CONFIRM":

        yes_words = [
            "yes",
            "yes please",
            "confirm",
            "confirmed",
            "y",
            "ok",
            "okay",
        ]

        no_words = [
            "no",
            "nope",
            "cancel",
            "n",
        ]


        # -------------------------------------------------
        # CONFIRM
        # -------------------------------------------------

        if text_lower in yes_words:

            registration = (
                st.session_state.registration
            )

            result = backend_register(
                {
                    "name": registration["name"],
                    "email": registration["email"],
                    "phone": registration["phone"],
                    "domain": registration["domain"],
                    "duration": registration["duration"],
                }
            )


            if result.get("success"):

                saved_registration = result.get(
                    "registration",
                    {}
                )

                registration_id = (
                    saved_registration.get(
                        "Registration_ID",
                        "N/A"
                    )
                )

                add_bot_message(
                    "🎉 **Registration successful!**\n\n"
                    "Your Registration ID is:\n\n"
                    f"### `{registration_id}`\n\n"
                    "Please keep this ID safe for checking your "
                    "status or editing/cancelling your registration later."
                )

                reset_registration()

                st.session_state.mode = None


            else:

                message = result.get(
                    "message",
                    "Registration could not be completed."
                )

                if "already exists" in message.lower():

                    add_bot_message(
                        "⚠️ **Registration already exists.**\n\n"
                        "A registration with this email address "
                        "or phone number already exists.\n\n"
                        "You can use **check status** to view it."
                    )

                    st.session_state.mode = None

                else:

                    add_bot_message(
                        "❌ **Registration failed.**\n\n"
                        f"{message}"
                    )


        # -------------------------------------------------
        # CANCEL CONFIRMATION
        # -------------------------------------------------

        elif text_lower in no_words:

            reset_registration()

            st.session_state.mode = None

            add_bot_message(
                "Registration cancelled. 👍\n\n"
                "You can start again anytime by typing **register**."
            )


        # -------------------------------------------------
        # INVALID CONFIRMATION
        # -------------------------------------------------

        else:

            add_bot_message(
                "Please type **Yes** to confirm your registration "
                "or **No** to cancel."
            )


        st.rerun()


    # =====================================================
    # CHECK STATUS
    # =====================================================

    if st.session_state.mode == "CHECK":

        result = backend_check(
            user_input
        )

        if result.get("success"):

            registration = result.get(
                "registration",
                {}
            )

            registration_id = registration.get(
                "Registration_ID",
                "N/A"
            )

            name = registration.get(
                "Name",
                "N/A"
            )

            email = registration.get(
                "Email",
                "N/A"
            )

            phone = registration.get(
                "Phone",
                "N/A"
            )

            domain = registration.get(
                "Domain",
                "N/A"
            )

            duration = registration.get(
                "Duration",
                "N/A"
            )

            status = registration.get(
                "Status",
                "N/A"
            )

            add_bot_message(
                "📋 **Registration Found!**\n\n"
                f"🆔 **Registration ID:** `{registration_id}`\n\n"
                f"👤 **Name:** {name}\n\n"
                f"📧 **Email:** {email}\n\n"
                f"📱 **Phone:** {phone}\n\n"
                f"🎯 **Domain:** {domain}\n\n"
                f"⏱️ **Duration:** {duration}\n\n"
                f"📌 **Status:** **{status}**"
            )

        else:

            add_bot_message(
                "❌ **Registration not found.**\n\n"
                "Please provide your Registration ID, "
                "email address or registered phone number."
            )

        st.session_state.mode = None

        st.rerun()


    # =====================================================
    # EDIT REGISTRATION - IDENTIFIER
    # =====================================================

    if st.session_state.mode == "EDIT":

        result = backend_check(
            user_input
        )

        if result.get("success"):

            registration = result.get(
                "registration",
                {}
            )

            registration_id = registration.get(
                "Registration_ID",
                user_input
            )

            st.session_state.edit_data = {
                "identifier": registration_id
            }

            add_bot_message(
                "✏️ **Registration found.**\n\n"
                "What would you like to edit?\n\n"
                "Type **domain** or **duration**."
            )

            st.session_state.mode = "EDIT_FIELD"

        else:

            add_bot_message(
                "❌ I couldn't find that registration.\n\n"
                "Please provide a valid Registration ID, "
                "email address or registered phone number."
            )

            st.session_state.mode = None

        st.rerun()


    # =====================================================
    # EDIT REGISTRATION - FIELD
    # =====================================================

    if st.session_state.mode == "EDIT_FIELD":

        if "domain" in text_lower:

            st.session_state.edit_data["field"] = "domain"

            add_bot_message(
                "Sure! 🎯\n\n"
                "Enter your new domain:\n\n"
                + "\n".join(
                    [
                        f"• {domain}"
                        for domain in DOMAINS
                    ]
                )
            )

            st.session_state.mode = "EDIT_VALUE"

        elif "duration" in text_lower:

            st.session_state.edit_data["field"] = "duration"

            add_bot_message(
                "Sure! ⏱️\n\n"
                "Enter your new duration.\n\n"
                "Example: `1 month`"
            )

            st.session_state.mode = "EDIT_VALUE"

        else:

            add_bot_message(
                "Please type **domain** or **duration**."
            )

        st.rerun()


    # =====================================================
    # EDIT REGISTRATION - VALUE
    # =====================================================

    if st.session_state.mode == "EDIT_VALUE":

        field = st.session_state.edit_data.get(
            "field"
        )

        identifier = st.session_state.edit_data.get(
            "identifier"
        )

        if field == "domain":

            value = get_domain(
                user_input
            )

            if not value:

                add_bot_message(
                    "Please enter a valid domain from the list."
                )

            else:

                result = backend_edit(
                    identifier,
                    {
                        "Domain": value
                    }
                )

                if result.get("success"):

                    add_bot_message(
                        "✅ **Domain updated successfully!**\n\n"
                        f"New domain: **{value}**"
                    )

                    st.session_state.mode = None
                    st.session_state.edit_data = {}

                else:

                    add_bot_message(
                        "❌ Unable to update your registration.\n\n"
                        f"{result.get('message', 'Unknown error')}"
                    )

        elif field == "duration":

            value = get_duration(
                user_input
            )

            if not value:

                add_bot_message(
                    "Please enter a valid duration.\n\n"
                    "Example: `1 month`"
                )

            else:

                result = backend_edit(
                    identifier,
                    {
                        "Duration": value
                    }
                )

                if result.get("success"):

                    add_bot_message(
                        "✅ **Duration updated successfully!**\n\n"
                        f"New duration: **{value}**"
                    )

                    st.session_state.mode = None
                    st.session_state.edit_data = {}

                else:

                    add_bot_message(
                        "❌ Unable to update your registration.\n\n"
                        f"{result.get('message', 'Unknown error')}"
                    )

        else:

            add_bot_message(
                "Something went wrong with the edit process."
            )

            st.session_state.mode = None
            st.session_state.edit_data = {}

        st.rerun()


    # =====================================================
    # CANCEL REGISTRATION - IDENTIFIER
    # =====================================================

    if st.session_state.mode == "CANCEL":

        result = backend_check(
            user_input
        )

        if result.get("success"):

            registration = result.get(
                "registration",
                {}
            )

            registration_id = registration.get(
                "Registration_ID",
                user_input
            )

            st.session_state.edit_data = {
                "identifier": registration_id
            }

            add_bot_message(
                "⚠️ **Registration found.**\n\n"
                "Are you sure you want to cancel this registration?\n\n"
                "Type **Yes** to confirm or **No** to keep it."
            )

            st.session_state.mode = "CANCEL_CONFIRM"

        else:

            add_bot_message(
                "❌ I couldn't find that registration.\n\n"
                "Please provide your Registration ID, "
                "email address or registered phone number."
            )

            st.session_state.mode = None

        st.rerun()


    # =====================================================
    # CANCEL CONFIRMATION
    # =====================================================

    if st.session_state.mode == "CANCEL_CONFIRM":

        identifier = st.session_state.edit_data.get(
            "identifier"
        )

        if text_lower in [
            "yes",
            "y",
            "confirm",
            "confirmed",
        ]:

            result = backend_cancel(
                identifier
            )

            if result.get("success"):

                add_bot_message(
                    "✅ **Registration cancelled successfully.**"
                )

            else:

                add_bot_message(
                    "❌ Unable to cancel the registration.\n\n"
                    f"{result.get('message', 'Unknown error')}"
                )

            st.session_state.mode = None
            st.session_state.edit_data = {}

        elif text_lower in [
            "no",
            "n",
            "nope",
        ]:

            add_bot_message(
                "Okay 👍 Your registration has not been cancelled."
            )

            st.session_state.mode = None
            st.session_state.edit_data = {}

        else:

            add_bot_message(
                "Please type **Yes** to cancel or **No** to keep your registration."
            )

        st.rerun()


    # =====================================================
    # NORMAL INTENT PROCESSING
    # =====================================================

    intent = classify_intent(
        user_input
    )


    # =====================================================
    # REGISTER
    # =====================================================

    if intent == "REGISTER":

        start_registration()

        st.rerun()


    # =====================================================
    # CHECK
    # =====================================================

    if intent == "CHECK":

        add_bot_message(
            "Sure! 🔎\n\n"
            "Please enter your **Registration ID**, "
            "registered **email address**, or "
            "registered **phone number**."
        )

        st.session_state.mode = "CHECK"

        st.rerun()


    # =====================================================
    # EDIT
    # =====================================================

    if intent == "EDIT":

        add_bot_message(
            "Sure! ✏️\n\n"
            "Please enter your **Registration ID**, "
            "registered **email address**, or "
            "registered **phone number**."
        )

        st.session_state.mode = "EDIT"

        st.rerun()


    # =====================================================
    # CANCEL
    # =====================================================

    if intent == "CANCEL":

        add_bot_message(
            "Sure. ⚠️\n\n"
            "Please enter your **Registration ID**, "
            "registered **email address**, or "
            "registered **phone number**."
        )

        st.session_state.mode = "CANCEL"

        st.rerun()


    # =====================================================
    # GREETING
    # =====================================================

    if intent == "GREETING":

        add_bot_message(
            "Hello! 👋😊\n\n"
            "I'm your AI Registration Assistant.\n\n"
            "You can ask me to:\n"
            "• Register for an internship\n"
            "• Check registration status\n"
            "• Edit registration\n"
            "• Cancel registration\n"
            "• Check eligibility\n"
            "• Ask about internship domains"
        )

        st.rerun()


    # =====================================================
    # THANK YOU
    # =====================================================

    if intent == "THANK_YOU":

        add_bot_message(
            "You're welcome! 😊\n\n"
            "I'm happy to help."
        )

        st.rerun()


    # =====================================================
    # HELP
    # =====================================================

    if intent == "HELP":

        add_bot_message(
            "I can help you with:\n\n"
            "📝 **Registration** — type `register`\n\n"
            "🔎 **Status** — type `check status`\n\n"
            "✏️ **Edit** — type `edit registration`\n\n"
            "❌ **Cancel** — type `cancel registration`\n\n"
            "🎓 **Eligibility** — type `eligibility`\n\n"
            "💬 Or ask me any internship-related question."
        )

        st.rerun()


    # =====================================================
    # ELIGIBILITY
    # =====================================================

    if intent == "ELIGIBILITY":

        add_bot_message(
            "🎓 **Eligibility Information**\n\n"
            "Eligibility can depend on the specific internship "
            "program and its requirements.\n\n"
            "Please check the official internship requirements "
            "for the exact eligibility criteria."
        )

        st.rerun()


    # =====================================================
    # GENERAL / GEMINI
    # =====================================================

    response = ask_ai(
        user_input
    )

    add_bot_message(
        response
    )

    st.rerun()