export default function Research() {
  return (
    <div className="page">
      <h2 className="gradient-text">Research Behind Voice AI</h2>

      <div className="glass-card" style={{ marginBottom: 18 }}>
        <h4 style={{ marginTop: 0 }}>Siri, Alexa, and Other Digital Assistants: A Study of Customer
          Satisfaction with Artificial Intelligence Applications (2019)</h4>
        <ul style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
          <li>Based on 244 survey responses.</li>
          <li>Siri accounted for about 72% of respondents' reported digital-assistant usage; Alexa about 13%.</li>
          <li>Expectations and confirmation of expectations were found to matter for customer satisfaction.</li>
          <li>Trust and privacy were examined as important contributing factors.</li>
        </ul>
      </div>

      <div className="glass-card">
        <h4 style={{ marginTop: 0 }}>"Hey, Alexa" "Hey, Siri", "OK Google" — Exploring Teenagers'
          Interaction with AI-Enabled Voice Assistants During COVID-19 (2023)</h4>
        <ul style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
          <li>36 teenagers aged 13–15 were interviewed, including Indian teenagers specifically.</li>
          <li>Used the UTAUT2 theoretical framework for technology adoption.</li>
          <li>Performance expectancy, effort expectancy, social influence, facilitating conditions,
            hedonic motivation, habit, and privacy concerns were found to influence usage.</li>
        </ul>
      </div>

      <p style={{ color: 'var(--muted)', fontSize: '0.8rem', marginTop: 18 }}>
        Note: these studies inform understanding of user adoption, satisfaction, and privacy
        perceptions around voice assistants. They do not describe, and this project does not claim
        to replicate, the proprietary internal architectures of Siri or Alexa.
      </p>
    </div>
  );
}
