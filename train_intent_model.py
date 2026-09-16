from intent_model import IntentClassifier


classifier = IntentClassifier()


test_messages = [

    # Greeting
    "hello",
    "hii",
    "good morning",

    # Registration
    "I want to register for an internship",
    "I want to apply for Data Science internship",

    # Check
    "check my registration",
    "where is my application",

    # Edit
    "I want to change my internship domain",
    "update my registration",

    # Cancel
    "cancel my application",
    "I want to cancel my registration",

    # Eligibility
    "am I eligible for this internship",
    "what are the internship requirements",

    # Help
    "I need help",
    "can you help me",

    # Thank you
    "thank you",
    "thanks a lot",

    # General
    "what is machine learning",
    "I want to know something",
    "I have a question"
]


print("\n" + "=" * 70)
print("AI INTERNSHIP CHATBOT - INTENT CLASSIFICATION TEST")
print("=" * 70)


for message in test_messages:

    intent, confidence = (
        classifier.predict_with_threshold(
            message
        )
    )

    print("\nUser:", message)
    print("Intent:", intent)
    print(
        f"Confidence: {confidence:.2%}"
    )


print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)