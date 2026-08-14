"""
Standalone evaluation report generator. Reads models/metrics.json (written
by train_intent.py / train_ner.py) and prints a clean summary. Also computes
ASR WER and translation BLEU IF reference files are provided — otherwise
honestly reports "Not evaluated yet" rather than inventing numbers.

Usage:
    python training/evaluate.py
    python training/evaluate.py --asr_refs data/asr_refs.json --asr_hyps data/asr_hyps.json
    python training/evaluate.py --mt_refs data/mt_refs.txt --mt_hyps data/mt_hyps.txt
"""
import argparse
import json
import os


def wer(reference: str, hypothesis: str) -> float:
    r, h = reference.split(), hypothesis.split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            cost = 0 if r[i - 1] == h[j - 1] else 1
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + cost)
    return d[-1][-1] / max(1, len(r))


def main(args):
    metrics = {}
    if os.path.exists("models/metrics.json"):
        with open("models/metrics.json") as f:
            metrics = json.load(f)

    print("=== Intent Classification ===")
    print(json.dumps(metrics.get("intent", "Not evaluated yet"), indent=2))

    print("\n=== NER ===")
    print(json.dumps(metrics.get("ner", "Not evaluated yet"), indent=2))

    if args.asr_refs and args.asr_hyps:
        with open(args.asr_refs) as f:
            refs = json.load(f)
        with open(args.asr_hyps) as f:
            hyps = json.load(f)
        scores = [wer(r, h) for r, h in zip(refs, hyps)]
        metrics["asr_wer"] = sum(scores) / len(scores) if scores else "Not evaluated yet"
    else:
        metrics.setdefault("asr_wer", "Not evaluated yet")

    if args.mt_refs and args.mt_hyps:
        try:
            from sacrebleu import corpus_bleu
            with open(args.mt_refs) as f:
                refs = [f.read().splitlines()]
            with open(args.mt_hyps) as f:
                hyps = f.read().splitlines()
            metrics["translation_bleu"] = corpus_bleu(hyps, refs).score
        except ImportError:
            print("Install sacrebleu to compute BLEU: pip install sacrebleu")
    else:
        metrics.setdefault("translation_bleu", "Not evaluated yet")

    with open("models/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print("\n=== ASR WER ===")
    print(metrics["asr_wer"])
    print("\n=== Translation BLEU ===")
    print(metrics["translation_bleu"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--asr_refs")
    parser.add_argument("--asr_hyps")
    parser.add_argument("--mt_refs")
    parser.add_argument("--mt_hyps")
    main(parser.parse_args())
