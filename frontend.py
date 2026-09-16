import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Internship Registration Assistant",
    page_icon="🎓",
    layout="centered"
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3.6-flash"

EXCEL_FILE = "registrations.xlsx"


# =========================================================
# INTERNSHIP DOMAINS
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
# EXCEL COLUMNS
# =========================================================

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
# EXCEL FUNCTIONS
# =========================================================

def initialize_excel():
    """
    Create registrations.xlsx if it does not exist.
    Also make sure all required columns are available.
    """

    if not os.path.exists(EXCEL_FILE):

        df = pd.DataFrame(columns=REQUIRED_COLUMNS)

        df.to_excel(
            EXCEL_FILE,
            index=False
        )

    else:

        try:
            df = pd.read_excel(EXCEL_FILE)

        except Exception:
            df = pd.DataFrame()

        changed = False

        for column in REQUIRED_COLUMNS:

            if column not in df.columns:

                df[column] = ""
                changed = True

        if changed:

            df = df[REQUIRED_COLUMNS]

            df.to_excel(
                EXCEL_FILE,
                index=False
            )


def load_data():

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


def save_data(df):

    df.to_excel(
        EXCEL_FILE,
        index=False
    )


# =========================================================
# VALIDATION FUNCTIONS
# =========================================================

def valid_email(email):

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    return bool(
        re.match(
            pattern,
            email.strip()
        )
    )


def valid_phone(phone):

    phone = phone.strip()

    return bool(
        re.fullmatch(
            r"[6-9]\d{9}",
            phone
        )
    )


def valid_duration(duration):

    pattern = r"^\d+\s*(day|days|week|weeks|month|months)$"

    return bool(
        re.fullmatch(
            pattern,
            duration.strip().lower()
        )
    )


def find_domain(text):

    text_lower = text.lower().strip()

    # Exact domain matching
    for domain in DOMAINS:

        if domain.lower() in text_lower:

            return domain

    # Short forms
    if re.search(r"\bdata science\b", text_lower):
        return "Data Science"

    if re.search(r"\bdata analytics\b", text_lower):
        return "Data Analytics"

    if re.search(r"\bartificial intelligence\b", text_lower):
        return "Artificial Intelligence"

    if re.search(r"\bmachine learning\b", text_lower):
        return "Machine Learning"

    if re.search(r"\bpython\b", text_lower):
        return "Python Development"

    if re.search(r"\bweb development\b", text_lower):
        return "Web Development"

    if re.search(r"\bfull stack\b", text_lower):
        return "Full Stack Development"

    if re.search(r"\bjava\b", text_lower):
        return "Java Development"

    if re.search(r"\bcloud\b", text_lower):
        return "Cloud Computing"

    if re.search(r"\bcyber\b", text_lower):
        return "Cyber Security"

    if re.search(r"\bandroid\b", text_lower):
        return "Android Development"

    return None


# =========================================================
# REGISTRATION ID
# =========================================================

def generate_registration_id():

    df = load_data()

    if df.empty:
        return "REG001"

    numbers = []

    for value in df["Registration_ID"]:

        if pd.isna(value):
            continue

        match = re.search(
            r"REG(\d+)",
            str(value)
        )

        if match:

            numbers.append(
                int(match.group(1))
            )

    if not numbers:

        return "REG001"

    next_number = max(numbers) + 1

    return f"REG{next_number:03d}"


# =========================================================
# FIND REGISTRATION
# =========================================================

def find_registration(identifier):

    df = load_data()

    if df.empty:
        return None

    identifier = identifier.strip()

    # Registration ID
    matches = df[
        df["Registration_ID"]
        .astype(str)
        .str.lower()
        == identifier.lower()
    ]

    if not matches.empty:

        return matches.index[0]

    # Email
    matches = df[
        df["Email"]
        .astype(str)
        .str.lower()
        == identifier.lower()
    ]

    if not matches.empty:

        return matches.index[0]

    # Phone
    matches = df[
        df["Phone"]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False
        )
        == identifier
    ]

    if not matches.empty:

        return matches.index[0]

    return None


# =========================================================
# DUPLICATE REGISTRATION
# =========================================================

def registration_exists(email, phone):

    df = load_data()

    if df.empty:
        return False

    active_df = df[
        df["Status"]
        .astype(str)
        .str.lower()
        != "cancelled"
    ]

    if active_df.empty:
        return False

    email_exists = (
        active_df["Email"]
        .astype(str)
        .str.lower()
        == email.lower()
    ).any()

    phone_exists = (
        active_df["Phone"]
        .astype(str)
        .str.replace(
            ".0",
            "",
            regex=False
        )
        == phone
    ).any()

    return email_exists or phone_exists


# =========================================================
# GEMINI
# =========================================================

def ask_gemini(question):

    if not API_KEY:

        return (
            "Gemini API key is not configured. "
            "Please check your .env file."
        )

    try:

        client = genai.Client(
            api_key=API_KEY
        )

        prompt = f"""
You are an Internship Registration Assistant.

Your job is to help students with questions about internships.

Available internship domains:
- Data Science
- Data Analytics
- Artificial Intelligence
- Machine Learning
- Python Development
- Web Development
- Full Stack Development
- Java Development
- Cloud Computing
- Cyber Security
- Android Development

Available features:
- New registration
- Check registration
- Edit registration
- Cancel registration
- Eligibility information
- Internship domains
- Internship duration
- General internship questions

Answer the student's question clearly and professionally.

Do not invent registration details.

Student question:
{question}
"""

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        if response and response.text:

            return response.text.strip()

        return (
            "Sorry, I could not generate a response "
            "right now."
        )

    except Exception as e:

        return (
            "Sorry, I couldn't process that right now. "
            "You can ask me about registration, "
            "eligibility, status, editing or cancellation."
        )


# =========================================================
# INTENT DETECTION
# =========================================================

def detect_intent(text):

    text_lower = text.lower().strip()


    # =====================================================
    # ISSUE / PROBLEM
    # IMPORTANT: THIS MUST COME FIRST
    # =====================================================

    issue_phrases = [

        "i have issue",
        "i have an issue",
        "i have a issue",

        "i have problem",
        "i have a problem",
        "i have an problem",

        "there is an issue",
        "there is a issue",

        "there is a problem",
        "there is a problem",

        "issue regarding",
        "problem regarding",

        "issue with this internship",
        "problem with this internship",

        "issue with internship",
        "problem with internship",

        "internship issue",
        "internship problem",

        "facing an issue",
        "facing a issue",

        "facing an problem",
        "facing a problem"
    ]

    if any(
        phrase in text_lower
        for phrase in issue_phrases
    ):

        return "ISSUE"


    # =====================================================
    # CANCEL
    # =====================================================

    cancel_phrases = [

        "cancel registration",
        "cancel my registration",
        "cancel internship registration",
        "cancel my internship",
        "i want to cancel",
        "i want cancel",
        "please cancel"
    ]

    if any(
        phrase in text_lower
        for phrase in cancel_phrases
    ):

        return "CANCEL"


    # =====================================================
    # EDIT
    # =====================================================

    edit_phrases = [

        "edit registration",
        "edit my registration",
        "change registration",
        "change my registration",
        "update registration",
        "update my registration",
        "modify registration",
        "modify my registration"
    ]

    if any(
        phrase in text_lower
        for phrase in edit_phrases
    ):

        return "EDIT"


    # =====================================================
    # CHECK
    # =====================================================

    check_phrases = [

        "check registration",
        "check my registration",
        "registration status",
        "check status",
        "my registration",
        "registration details",
        "show my registration"
    ]

    if any(
        phrase in text_lower
        for phrase in check_phrases
    ):

        return "CHECK"


    # =====================================================
    # ELIGIBILITY
    # =====================================================

    eligibility_phrases = [

        "eligibility",
        "eligible",
        "qualification",
        "qualifications",
        "who can apply",
        "can i apply",
        "am i eligible"
    ]

    if any(
        phrase in text_lower
        for phrase in eligibility_phrases
    ):

        return "ELIGIBILITY"


    # =====================================================
    # REGISTER
    # =====================================================

    register_phrases = [

        "register",
        "registration",
        "apply",
        "application",
        "enroll",
        "enrol",
        "join internship",
        "i want internship",
        "i want to apply",
        "i want to register"
    ]

    if any(
        phrase in text_lower
        for phrase in register_phrases
    ):

        return "REGISTER"


    # =====================================================
    # GREETING
    # =====================================================

    greetings = [

        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "helo",
        "good morning",
        "good afternoon",
        "good evening"
    ]

    if text_lower in greetings:

        return "GREETING"


    # =====================================================
    # THANK YOU
    # =====================================================

    thank_phrases = [

        "thank you",
        "thanks",
        "thankyou",
        "thx"
    ]

    if any(
        phrase in text_lower
        for phrase in thank_phrases
    ):

        return "THANK_YOU"


    # =====================================================
    # HELP
    # =====================================================

    help_phrases = [

        "help",
        "help me",
        "what can you do",
        "how can you help me"
    ]

    if any(
        phrase in text_lower
        for phrase in help_phrases
    ):

        return "HELP"


    # =====================================================
    # GENERAL
    # =====================================================

    return "GENERAL"


# =========================================================
# CHAT FUNCTIONS
# =========================================================

def add_message(role, content):

    st.session_state.messages.append(
        {
            "role": role,
            "content": content
        }
    )


def reset_registration():

    st.session_state.mode = None

    st.session_state.registration = {}

    st.session_state.edit_index = None

    st.session_state.edit_field = None


def start_registration():

    st.session_state.mode = "REGISTER"

    st.session_state.registration = {}

    st.session_state.edit_index = None

    st.session_state.edit_field = None


# =========================================================
# REGISTRATION FLOW
# =========================================================

def handle_registration(user_input):

    data = st.session_state.registration

    text = user_input.strip()


    # =====================================================
    # ISSUE DURING REGISTRATION
    # =====================================================

    issue_phrases = [

        "i have issue",
        "i have an issue",
        "i have a issue",
        "i have problem",
        "i have a problem",
        "there is an issue",
        "there is a problem",
        "issue regarding",
        "problem regarding"
    ]

    if any(
        phrase in text.lower()
        for phrase in issue_phrases
    ):

        return (
            "Sure! 😊 No problem.\n\n"
            "Please describe the issue you are facing "
            "regarding the internship.\n\n"
            "You can tell me if the issue is related to:\n"
            "- Registration\n"
            "- Eligibility\n"
            "- Internship domain\n"
            "- Internship duration\n"
            "- Offer letter\n"
            "- Certificate\n"
            "- Application status\n"
            "- Something else\n\n"
            "I'll help you with it."
        )


    # =====================================================
    # CANCEL DURING REGISTRATION
    # =====================================================

    if any(
        phrase in text.lower()
        for phrase in [
            "cancel",
            "stop registration",
            "exit registration"
        ]
    ):

        reset_registration()

        return (
            "Registration cancelled. 😊\n\n"
            "If you want to register later, "
            "just type **register**."
        )


    # =====================================================
    # NAME
    # =====================================================

    if "name" not in data:

        if len(text) < 2:

            return "Please enter your full name."

        data["name"] = text

        return (
            f"Nice to meet you, **{text}**! 😊\n\n"
            "Please enter your email address."
        )


    # =====================================================
    # EMAIL
    # =====================================================

    if "email" not in data:

        if not valid_email(text):

            return (
                "Please enter a valid email address.\n\n"
                "Example: `student@gmail.com`"
            )

        data["email"] = text.lower()

        return (
            "Great! 👍\n\n"
            "Now please enter your 10-digit "
            "mobile number."
        )


    # =====================================================
    # PHONE
    # =====================================================

    if "phone" not in data:

        phone = re.sub(
            r"\D",
            "",
            text
        )

        if not valid_phone(phone):

            return (
                "Please enter a valid 10-digit Indian "
                "mobile number starting with 6, 7, 8 or 9."
            )

        data["phone"] = phone

        domain_list = "\n".join(
            f"- {domain}"
            for domain in DOMAINS
        )

        return (
            "Perfect! 📱\n\n"
            "Please select your internship domain.\n\n"
            f"{domain_list}\n\n"
            "You can type the domain name, for example "
            "**Data Science**."
        )


    # =====================================================
    # DOMAIN
    # =====================================================

    if "domain" not in data:

        domain = find_domain(text)

        if not domain:

            return (
                "Please choose one of the available "
                "internship domains:\n\n"
                + "\n".join(
                    f"- {d}"
                    for d in DOMAINS
                )
            )

        data["domain"] = domain

        return (
            f"Excellent choice! 🎯\n\n"
            f"Selected domain: **{domain}**\n\n"
            "Now enter your preferred internship duration.\n\n"
            "Examples:\n"
            "- 1 month\n"
            "- 2 months\n"
            "- 4 weeks"
        )


    # =====================================================
    # DURATION
    # =====================================================

    if "duration" not in data:

        if not valid_duration(text):

            return (
                "Please enter the duration in a valid format.\n\n"
                "Examples:\n"
                "- 1 month\n"
                "- 2 months\n"
                "- 4 weeks\n"
                "- 15 days"
            )

        data["duration"] = text

        return (
            "Almost done! 🎉\n\n"
            "**Please confirm your registration:**\n\n"
            f"👤 Name: **{data['name']}**\n\n"
            f"📧 Email: **{data['email']}**\n\n"
            f"📱 Phone: **{data['phone']}**\n\n"
            f"🎓 Domain: **{data['domain']}**\n\n"
            f"⏱️ Duration: **{data['duration']}**\n\n"
            "Do you want to confirm this registration?\n\n"
            "Please type **Yes** or **No**."
        )


    # =====================================================
    # CONFIRMATION
    # =====================================================

    if "duration" in data:

        lower_text = text.lower().strip()


        # ISSUE AT CONFIRMATION
        if any(
            phrase in lower_text
            for phrase in [
                "i have issue",
                "i have an issue",
                "i have a issue",
                "i have problem",
                "i have a problem",
                "issue regarding",
                "problem regarding"
            ]
        ):

            return (
                "Sure! 😊 No problem.\n\n"
                "Please describe the issue you are facing "
                "regarding the internship, and I'll help you."
            )


        if lower_text in [
            "yes",
            "y",
            "confirm",
            "confirmed",
            "okay",
            "ok"
        ]:

            return save_registration()


        if lower_text in [
            "no",
            "n",
            "cancel"
        ]:

            reset_registration()

            return (
                "No problem. 😊\n\n"
                "Your registration was not submitted.\n"
                "You can start again anytime by typing "
                "**register**."
            )


        return (
            "Please type **Yes** to confirm or **No** "
            "to cancel the registration."
        )


# =========================================================
# SAVE REGISTRATION
# =========================================================

def save_registration():

    data = st.session_state.registration

    email = data["email"]

    phone = data["phone"]


    # Duplicate check

    if registration_exists(
        email,
        phone
    ):

        return (
            "⚠️ A registration already exists with "
            "this email address or phone number.\n\n"
            "Please use your existing registration to "
            "check or edit it."
        )


    df = load_data()


    registration_id = generate_registration_id()


    new_row = {

        "Registration_ID":
            registration_id,

        "Name":
            data["name"],

        "Email":
            data["email"],

        "Phone":
            data["phone"],

        "Domain":
            data["domain"],

        "Duration":
            data["duration"],

        "Status":
            "Active",

        "Created_At":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
    }


    df = pd.concat(
        [
            df,
            pd.DataFrame([new_row])
        ],
        ignore_index=True
    )


    save_data(df)


    reset_registration()


    return (
        "🎉 **Registration Successful!**\n\n"
        f"Your Registration ID is: "
        f"**{registration_id}**\n\n"
        "Please save this Registration ID for "
        "future reference.\n\n"
        "You can use it to:\n"
        "- Check your registration\n"
        "- Edit your registration\n"
        "- Cancel your registration\n\n"
        "Thank you for registering! 😊"
    )


# =========================================================
# CHECK REGISTRATION
# =========================================================

def handle_check(user_input):

    index = find_registration(
        user_input
    )

    if index is None:

        return (
            "❌ I couldn't find a registration with "
            "that Registration ID, email or phone number.\n\n"
            "Please check the details and try again."
        )

    df = load_data()

    row = df.loc[index]


    if str(row["Status"]).lower() == "cancelled":

        status_text = "Cancelled ❌"

    else:

        status_text = "Active ✅"


    return (
        "### 📋 Registration Details\n\n"
        f"**Registration ID:** "
        f"{row['Registration_ID']}\n\n"
        f"**Name:** {row['Name']}\n\n"
        f"**Email:** {row['Email']}\n\n"
        f"**Phone:** {row['Phone']}\n\n"
        f"**Domain:** {row['Domain']}\n\n"
        f"**Duration:** {row['Duration']}\n\n"
        f"**Status:** {status_text}\n\n"
        f"**Created At:** {row['Created_At']}"
    )


# =========================================================
# EDIT REGISTRATION
# =========================================================

def handle_edit(user_input):

    # Step 1: Find registration

    if st.session_state.edit_index is None:

        index = find_registration(
            user_input
        )

        if index is None:

            return (
                "❌ Registration not found.\n\n"
                "Please enter your Registration ID, "
                "email address or phone number."
            )

        df = load_data()

        if str(
            df.loc[index, "Status"]
        ).lower() == "cancelled":

            return (
                "❌ This registration has already been "
                "cancelled and cannot be edited."
            )

        st.session_state.edit_index = index

        return (
            "Registration found! ✅\n\n"
            "What would you like to edit?\n\n"
            "1. Name\n"
            "2. Email\n"
            "3. Phone\n"
            "4. Domain\n"
            "5. Duration\n\n"
            "Please type the field name."
        )


    # Step 2: Select field

    if st.session_state.edit_field is None:

        field_map = {

            "name": "Name",
            "email": "Email",
            "phone": "Phone",
            "domain": "Domain",
            "duration": "Duration",

            "1": "Name",
            "2": "Email",
            "3": "Phone",
            "4": "Domain",
            "5": "Duration"
        }

        field = field_map.get(
            user_input.lower().strip()
        )

        if field is None:

            return (
                "Please choose one of these fields:\n\n"
                "1. Name\n"
                "2. Email\n"
                "3. Phone\n"
                "4. Domain\n"
                "5. Duration"
            )

        st.session_state.edit_field = field

        return (
            f"Please enter the new **{field}**."
        )


    # Step 3: Save new value

    df = load_data()

    index = st.session_state.edit_index

    field = st.session_state.edit_field

    value = user_input.strip()


    if field == "Email":

        if not valid_email(value):

            return (
                "Please enter a valid email address."
            )

        value = value.lower()


    elif field == "Phone":

        value = re.sub(
            r"\D",
            "",
            value
        )

        if not valid_phone(value):

            return (
                "Please enter a valid 10-digit "
                "mobile number."
            )


    elif field == "Domain":

        domain = find_domain(value)

        if not domain:

            return (
                "Please enter a valid internship domain."
            )

        value = domain


    elif field == "Duration":

        if not valid_duration(value):

            return (
                "Please enter a valid duration.\n\n"
                "Example: 1 month"
            )


    df.loc[index, field] = value

    save_data(df)


    registration_id = df.loc[
        index,
        "Registration_ID"
    ]


    reset_registration()


    return (
        "✅ **Registration Updated Successfully!**\n\n"
        f"Your **{field}** has been updated.\n\n"
        f"Registration ID: **{registration_id}**"
    )


# =========================================================
# CANCEL REGISTRATION
# =========================================================

def handle_cancel(user_input):

    index = find_registration(
        user_input
    )

    if index is None:

        return (
            "❌ Registration not found.\n\n"
            "Please enter your Registration ID, "
            "email address or phone number."
        )


    df = load_data()


    if str(
        df.loc[index, "Status"]
    ).lower() == "cancelled":

        reset_registration()

        return (
            "This registration is already cancelled."
        )


    df.loc[
        index,
        "Status"
    ] = "Cancelled"


    save_data(df)


    registration_id = df.loc[
        index,
        "Registration_ID"
    ]


    reset_registration()


    return (
        "✅ **Registration Cancelled Successfully.**\n\n"
        f"Registration ID: **{registration_id}**\n\n"
        "If you want to register again in the future, "
        "just type **register**."
    )


# =========================================================
# NORMAL INTENT RESPONSE
# =========================================================

def handle_intent(
    user_input,
    intent
):


    # =====================================================
    # GREETING
    # =====================================================

    if intent == "GREETING":

        return (
            "Hello! 👋 I am your **Internship "
            "Registration Assistant**.\n\n"
            "I can help you with:\n\n"
            "• Registering for an internship\n"
            "• Checking your registration\n"
            "• Editing your registration\n"
            "• Cancelling your registration\n"
            "• Eligibility information\n"
            "• Internship domains and duration\n"
            "• General internship questions\n\n"
            "How can I assist you today?"
        )


    # =====================================================
    # ISSUE
    # =====================================================

    if intent == "ISSUE":

        return (
            "Sure! 😊 No problem.\n\n"
            "Please describe the issue you are facing "
            "regarding the internship.\n\n"
            "You can tell me if the issue is related to:\n"
            "- Registration\n"
            "- Eligibility\n"
            "- Internship domain\n"
            "- Internship duration\n"
            "- Offer letter\n"
            "- Certificate\n"
            "- Application status\n"
            "- Something else\n\n"
            "I'll help you with it."
        )


    # =====================================================
    # REGISTER
    # =====================================================

    if intent == "REGISTER":

        start_registration()

        return (
            "Great! 🎓 Let's start your internship "
            "registration.\n\n"
            "Please enter your **full name**."
        )


    # =====================================================
    # CHECK
    # =====================================================

    if intent == "CHECK":

        st.session_state.mode = "CHECK"

        return (
            "Sure! 🔎\n\n"
            "Please enter your **Registration ID**, "
            "registered email address or phone number."
        )


    # =====================================================
    # EDIT
    # =====================================================

    if intent == "EDIT":

        st.session_state.mode = "EDIT"

        st.session_state.edit_index = None

        st.session_state.edit_field = None

        return (
            "Sure! ✏️\n\n"
            "Please enter your **Registration ID**, "
            "registered email address or phone number."
        )


    # =====================================================
    # CANCEL
    # =====================================================

    if intent == "CANCEL":

        st.session_state.mode = "CANCEL"

        return (
            "I can help you cancel your registration.\n\n"
            "Please enter your **Registration ID**, "
            "registered email address or phone number."
        )


    # =====================================================
    # ELIGIBILITY
    # =====================================================

    if intent == "ELIGIBILITY":

        return (
            "### 🎓 Internship Eligibility\n\n"
            "Students and graduates who meet the "
            "requirements of the internship can apply.\n\n"
            "Typical requirements may include:\n\n"
            "• 10th qualification\n"
            "• 12th qualification\n"
            "• Graduation or relevant technical background\n"
            "• Interest in the selected internship domain\n\n"
            "Eligibility can vary depending on the "
            "specific internship."
        )


    # =====================================================
    # HELP
    # =====================================================

    if intent == "HELP":

        return (
            "Of course! 😊 I can help you with:\n\n"
            "🎓 **Registration**\n"
            "🔎 **Check Status**\n"
            "✏️ **Edit Registration**\n"
            "❌ **Cancel Registration**\n"
            "📚 **Eligibility**\n"
            "💻 **Internship Domains**\n"
            "⏱️ **Internship Duration**\n"
            "🤖 **General Internship Questions**\n\n"
            "Just tell me what you need."
        )


    # =====================================================
    # THANK YOU
    # =====================================================

    if intent == "THANK_YOU":

        return (
            "You're most welcome! 😊\n\n"
            "I'm happy to help."
        )


    # =====================================================
    # GENERAL → GEMINI
    # =====================================================

    return ask_gemini(
        user_input
    )


# =========================================================
# INITIALIZE
# =========================================================

initialize_excel()


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:

    st.session_state.messages = [

        {
            "role": "assistant",
            "content":
                "Hello! 👋 I am your **Internship "
                "Registration Assistant**.\n\n"
                "I can help you with:\n\n"
                "• Registering for an internship\n"
                "• Checking your registration\n"
                "• Editing your registration\n"
                "• Cancelling your registration\n"
                "• Eligibility information\n"
                "• Internship domains and duration\n"
                "• General internship questions\n\n"
                "How can I assist you today?"
        }

    ]


if "mode" not in st.session_state:

    st.session_state.mode = None


if "registration" not in st.session_state:

    st.session_state.registration = {}


if "edit_index" not in st.session_state:

    st.session_state.edit_index = None


if "edit_field" not in st.session_state:

    st.session_state.edit_field = None


# =========================================================
# TITLE
# =========================================================

st.title("🎓 Internship Registration Assistant")

st.caption(
    "AI-powered internship registration and support chatbot"
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📌 Available Services")

    st.write(
        """
        • New Registration

        • Check Registration

        • Edit Registration

        • Cancel Registration

        • Eligibility

        • Internship Domains

        • General Questions
        """
    )

    st.divider()

    st.write("**Available Domains:**")

    for domain in DOMAINS:

        st.write(
            f"• {domain}"
        )

    st.divider()

    if st.button(
        "🗑️ Clear Chat"
    ):

        st.session_state.messages = [

            {
                "role": "assistant",
                "content":
                    "Hello! 👋 I am your **Internship "
                    "Registration Assistant**.\n\n"
                    "How can I assist you today?"
            }

        ]

        reset_registration()

        st.rerun()


# =========================================================
# DISPLAY CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input(
    "Type your message here..."
)


# =========================================================
# PROCESS USER MESSAGE
# =========================================================

if user_input:

    user_input = user_input.strip()


    if not user_input:

        st.stop()


    # =====================================================
    # IMPORTANT:
    # DISPLAY USER MESSAGE IMMEDIATELY
    # =====================================================

    add_message(
        "user",
        user_input
    )


    with st.chat_message(
        "user"
    ):

        st.markdown(
            user_input
        )


    # =====================================================
    # PROCESS RESPONSE
    # =====================================================

    response = ""


    # =====================================================
    # ACTIVE REGISTRATION MODE
    # =====================================================

    if st.session_state.mode == "REGISTER":

        response = handle_registration(
            user_input
        )


    # =====================================================
    # CHECK MODE
    # =====================================================

    elif st.session_state.mode == "CHECK":

        response = handle_check(
            user_input
        )

        # End check mode after successful/attempted lookup
        if "couldn't find" not in response.lower():

            st.session_state.mode = None


    # =====================================================
    # EDIT MODE
    # =====================================================

    elif st.session_state.mode == "EDIT":

        response = handle_edit(
            user_input
        )


    # =====================================================
    # CANCEL MODE
    # =====================================================

    elif st.session_state.mode == "CANCEL":

        response = handle_cancel(
            user_input
        )


    # =====================================================
    # NORMAL CHAT
    # =====================================================

    else:

        intent = detect_intent(
            user_input
        )

        response = handle_intent(
            user_input,
            intent
        )


    # =====================================================
    # SAVE ASSISTANT MESSAGE
    # =====================================================

    add_message(
        "assistant",
        response
    )


    # =====================================================
    # DISPLAY ASSISTANT MESSAGE
    # =====================================================

    with st.chat_message(
        "assistant"
    ):

        st.markdown(
            response
        )