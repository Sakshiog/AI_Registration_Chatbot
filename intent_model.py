import json

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


class IntentClassifier:

    def __init__(self, intents_file="intents.json"):

        with open(
            intents_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        self.texts = []
        self.labels = []

        for intent in data["intents"]:

            for pattern in intent["patterns"]:

                self.texts.append(pattern)
                self.labels.append(intent["tag"])

        # Convert text into numerical features
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2)
        )

        # Machine Learning model
        self.model = LogisticRegression(
            max_iter=1000
        )

        self.train()

    def train(self):

        X = self.vectorizer.fit_transform(
            self.texts
        )

        self.model.fit(
            X,
            self.labels
        )

    def predict(self, text):

        X = self.vectorizer.transform(
            [text]
        )

        prediction = self.model.predict(X)

        return prediction[0]

    def predict_with_confidence(self, text):

        X = self.vectorizer.transform(
            [text]
        )

        prediction = self.model.predict(X)[0]

        probabilities = self.model.predict_proba(X)[0]

        confidence = max(probabilities)

        return prediction, confidence
