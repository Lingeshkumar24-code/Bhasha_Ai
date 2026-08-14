"""
Fine-tune IndicBERT (or XLM-R) for intent classification on data/intents.csv.

Usage:
    pip install -r training/requirements.txt
    python training/train_intent.py --base_model ai4bharat/indic-bert --epochs 8

This produces a real checkpoint at models/intent_classifier/, which
backend/app/services/intent_service.py will automatically detect and load
instead of the keyword fallback.

NOTE: This script needs internet access to the HuggingFace Hub and,
ideally, a GPU. It was NOT run inside the build sandbox that generated
this project (no Hub/GPU access there) — run it yourself to get real
metrics. Do not report accuracy numbers until you've actually run this.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix


def main(args):
    from datasets import Dataset
    from transformers import (
        AutoTokenizer, AutoModelForSequenceClassification,
        TrainingArguments, Trainer, DataCollatorWithPadding,
    )

    df = pd.read_csv(args.data_path)
    labels = sorted(df["intent"].unique())
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}
    df["label"] = df["intent"].map(label2id)

    train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42, stratify=df["label"])
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42, stratify=temp_df["label"])

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, padding=False)

    train_ds = Dataset.from_pandas(train_df[["text", "label"]]).map(tokenize, batched=True)
    val_ds = Dataset.from_pandas(val_df[["text", "label"]]).map(tokenize, batched=True)
    test_ds = Dataset.from_pandas(test_df[["text", "label"]]).map(tokenize, batched=True)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model, num_labels=len(labels), id2label=id2label, label2id=label2id
    )

    def compute_metrics(eval_pred):
        logits, y_true = eval_pred
        y_pred = np.argmax(logits, axis=-1)
        acc = accuracy_score(y_true, y_pred)
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
        return {"accuracy": acc, "precision": p, "recall": r, "f1": f1}

    training_args = TrainingArguments(
        output_dir="training/checkpoints/intent",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        logging_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()

    test_metrics = trainer.evaluate(test_ds)
    preds = trainer.predict(test_ds)
    y_pred = np.argmax(preds.predictions, axis=-1)
    cm = confusion_matrix(test_df["label"], y_pred).tolist()

    os.makedirs("models/intent_classifier", exist_ok=True)
    model.save_pretrained("models/intent_classifier")
    tokenizer.save_pretrained("models/intent_classifier")

    os.makedirs("models", exist_ok=True)
    existing = {}
    if os.path.exists("models/metrics.json"):
        with open("models/metrics.json") as f:
            existing = json.load(f)
    existing["intent"] = {
        "accuracy": test_metrics.get("eval_accuracy"),
        "precision": test_metrics.get("eval_precision"),
        "recall": test_metrics.get("eval_recall"),
        "f1": test_metrics.get("eval_f1"),
        "confusion_matrix": cm,
        "labels": labels,
    }
    with open("models/metrics.json", "w") as f:
        json.dump(existing, f, indent=2)

    print("Training complete. Real metrics written to models/metrics.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", default="ai4bharat/indic-bert")
    parser.add_argument("--data_path", default="data/intents.csv")
    parser.add_argument("--epochs", type=int, default=8)
    main(parser.parse_args())
