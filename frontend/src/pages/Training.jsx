export default function Training() {
  return (
    <div className="page">
      <h2 className="gradient-text">Train Your AI</h2>
      <p style={{ color: 'var(--muted)' }}>
        The intent classifier and NER model are fine-tuned with real HuggingFace Transformers
        training scripts against a dataset of multilingual, code-mixed examples.
      </p>
      <div className="glass-card">
        <h4>Dataset</h4>
        <pre>{`data/
  intents.csv        # text, intent, language
  ner_train.json      # span-annotated entities
  ner_validation.json
  ner_test.json`}</pre>
      </div>
      <div className="glass-card" style={{ marginTop: 16 }}>
        <h4>Run training</h4>
        <pre>{`pip install -r training/requirements.txt
python training/train_intent.py --base_model ai4bharat/indic-bert --epochs 8
python training/train_ner.py --base_model ai4bharat/indic-bert --epochs 10
python training/evaluate.py`}</pre>
        <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
          Checkpoints are written to <code>models/intent_classifier</code> and
          <code> models/ner_model</code>, and the backend auto-loads them on next restart —
          the frontend will then say "IndicBERT (fine-tuned)" instead of the keyword fallback.
        </p>
      </div>
    </div>
  );
}
