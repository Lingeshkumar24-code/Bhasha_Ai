import { Routes, Route } from 'react-router-dom';
import Nav from './components/Nav';
import Home from './pages/Home';
import VoiceAssistant from './pages/VoiceAssistant';
import LivePipeline from './pages/LivePipeline';
import NLPAnalyzer from './pages/NLPAnalyzer';
import ModelLab from './pages/ModelLab';
import Training from './pages/Training';
import Evaluation from './pages/Evaluation';
import AlexaVsSiri from './pages/AlexaVsSiri';
import IndiaChallenges from './pages/IndiaChallenges';
import Research from './pages/Research';
import Architecture from './pages/Architecture';
import About from './pages/About';

export default function App() {
  return (
    <div className="app-shell">
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/assistant" element={<VoiceAssistant />} />
        <Route path="/pipeline" element={<LivePipeline />} />
        <Route path="/nlp" element={<NLPAnalyzer />} />
        <Route path="/models" element={<ModelLab />} />
        <Route path="/training" element={<Training />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/alexa-vs-siri" element={<AlexaVsSiri />} />
        <Route path="/india-challenges" element={<IndiaChallenges />} />
        <Route path="/research" element={<Research />} />
        <Route path="/architecture" element={<Architecture />} />
        <Route path="/about" element={<About />} />
      </Routes>
      <div className="footer-note">
        BhashaVoice AI — Educational MCA Deep Learning project. Not affiliated with Apple or Amazon.
      </div>
    </div>
  );
}
