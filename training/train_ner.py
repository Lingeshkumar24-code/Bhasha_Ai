"""
Fine-tune IndicBERT/XLM-R with a token-classification head on the
data/ner_train.json (+validation/test) span-annotated entities.

Usage:
    pip install -r training/requirements.txt
    python training/train_ner.py --base_model ai4bharat/indic-bert --epochs 10

Produces models/ner_model/, auto-detected by app/services/ner_service.py.

Same caveat as train_intent.py: needs Hub access + ideally a GPU; wasn't
executed inside the build sandbox. Run it yourself before trusting numbers.
"""
import argparse
import json
import os

import numpy as np
from sklearn.metrics import precision_recall_fscore_support

LABELS = ["O", "B-PERSON", "I-PERSON", "B-LOCATION", "I-LOCATION", "B-DATE", "I-DATE",
          "B-TIME", "I-TIME", "B-MONEY", "I-MONEY", "B-ORGANIZATION", "I-ORGANIZATION",
          "B-LANGUAGE", "I-LANGUAGE", "B-DEVICE", "I-DEVICE", "B-SONG", "I-SONG", "B-CITY", "I-CITY"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}


def spans_to_bio(text, entities, tokenizer):
    encoding = tokenizer(text, return_offsets_mapping=True, truncation=True)
    labels = ["O"] * len(encoding["input_ids"])
    for ent in entities:
        started = False
        for i, (start, end) in enumerate(encoding["offset_mapping"]):
            if start == end:
                continue
            if start >= ent["start"] and end <= ent["end"]:
                labels[i] = f"{'B' if not started else 'I'}-{ent['label']}"
                started = True
    encoding.pop("offset_mapping")
    encoding["labels"] = [LABEL2ID.get(l, 0) for l in labels]
    return encoding


def load_split(path, tokenizer):
    with open(path) as f:
        raw = json.load(f)
    return [spans_to_bio(r["text"], r["entities"], tokenizer) for r in raw]


def main(args):
    from datasets import Dataset
    from transformers import (
        AutoTokenizer, AutoModelForTokenClassification,
        TrainingArguments, Trainer, DataCollatorForTokenClassification,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)

    train_data = load_split("data/ner_train.json", tokenizer)
    val_data = load_split("data/ner_validation.json", tokenizer)
    test_data = load_split("data/ner_test.json", tokenizer)

    train_ds = Dataset.from_list(train_data)
    val_ds = Dataset.from_list(val_data)
    test_ds = Dataset.from_list(test_data)

    model = AutoModelForTokenClassification.from_pretrained(
        args.base_model, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID
    )

    def compute_metrics(eval_pred):
        logits, y_true = eval_pred
        y_pred = np.argmax(logits, axis=-1)
        true_flat, pred_flat = [], []
        for t_row, p_row in zip(y_true, y_pred):
            for t, p in zip(t_row, p_row):
                if t != -100:
                    true_flat.append(t)
                    pred_flat.append(p)
        p, r, f1, _ = precision_recall_fscore_support(true_flat, pred_flat, average="weighted", zero_division=0)
        return {"precision": p, "recall": r, "f1": f1}

    training_args = TrainingArguments(
        output_dir="training/checkpoints/ner",
        num_train_epochs=args.epochs,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()
    test_metrics = trainer.evaluate(test_ds)

    os.makedirs("models/ner_model", exist_ok=True)
    model.save_pretrained("models/ner_model")
    tokenizer.save_pretrained("models/ner_model")

    existing = {}
    if os.path.exists("models/metrics.json"):
        with open("models/metrics.json") as f:
            existing = json.load(f)
    existing["ner"] = {
        "precision": test_metrics.get("eval_precision"),
        "recall": test_metrics.get("eval_recall"),
        "f1": test_metrics.get("eval_f1"),
        "labels": LABELS,
    }
    with open("models/metrics.json", "w") as f:
        json.dump(existing, f, indent=2)

    print("NER training complete. Real metrics written to models/metrics.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", default="ai4bharat/indic-bert")
    parser.add_argument("--epochs", type=int, default=10)
    main(parser.parse_args())
