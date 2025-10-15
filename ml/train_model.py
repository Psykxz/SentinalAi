import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH_1 = os.path.join(BASE_DIR, "cyberbullying_tweets.csv")
DATA_PATH_2 = os.path.join(BASE_DIR, "train.csv")
MODEL_PATH = os.path.join(BASE_DIR, "cyberbullying_model.pkl")

def train_model(dataset_paths, model_path=MODEL_PATH):
    combined_df = pd.DataFrame()

    for path in dataset_paths:
        df = pd.read_csv(path)
        
        if "cyberbullying_tweets.csv" in path:
            text_col = "tweet_text"
            label_col = "cyberbullying_type"
            df_cleaned = df[[text_col, label_col]].copy()
            df_cleaned.rename(columns={text_col: "text", label_col: "label"}, inplace=True)
            
        elif "train.csv" in path:
            text_col = "comment_text"
            toxic_cols = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
            df['is_toxic'] = df[toxic_cols].max(axis=1)
            df['label'] = df['is_toxic'].apply(lambda x: 'bullying' if x > 0 else 'not_cyberbullying')
            df_cleaned = df[[text_col, 'label']].copy()
            df_cleaned.rename(columns={text_col: "text"}, inplace=True)
            
        else:
            print(f"Warning: Skipping unknown dataset {path}")
            continue

        combined_df = pd.concat([combined_df, df_cleaned], ignore_index=True)

    # Fill any NaN values that might still exist after concatenation
    combined_df['text'] = combined_df['text'].fillna('')

    print("📊 Combined Dataset shape:", combined_df.shape)
    print("📑 Columns:", combined_df.columns.tolist())
    print(combined_df.head())

    X = combined_df["text"]
    y = combined_df["label"]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Pipeline: TF-IDF + Logistic Regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", max_features=5000)),
        ("clf", LogisticRegression(max_iter=300))
    ])

    # Train
    pipeline.fit(X_train, y_train)

    # Evaluate
    y_pred = pipeline.predict(X_test)
    print("\nClassification Report:\n", classification_report(y_test, y_pred))

    # Save model
    joblib.dump(pipeline, model_path)
    print(f"Model trained and saved to {model_path}")

if __name__ == "__main__":
    data_files = [
        DATA_PATH_1,
        DATA_PATH_2
    ]
    train_model(dataset_paths=data_files)