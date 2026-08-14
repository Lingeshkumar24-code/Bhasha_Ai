export default function About() {
  return (
    <div className="page">
      <h2 className="gradient-text">About This Project</h2>
      <div className="glass-card">
        <p>
          <b>BhashaVoice AI</b> is an MCA Deep Learning project demonstrating a complete
          multilingual voice-assistant pipeline built for Indian languages, with an emphasis
          on South Indian languages and code-mixed speech.
        </p>
        <p>
          It combines pretrained foundation models (browser ASR, Groq LLM, translation/TTS
          services) with our own fine-tuned models (intent classification, NER) trained on a
          custom multilingual dataset — see the Model Lab and Training pages for the honest
          breakdown of what's pretrained vs. what we trained ourselves.
        </p>
        <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
          This is an independent educational project. It is not affiliated with, and does not
          claim to replicate the proprietary technology of, Apple Siri or Amazon Alexa.
        </p>
      </div>
    </div>
  );
}
