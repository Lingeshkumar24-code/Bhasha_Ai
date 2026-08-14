import { NavLink } from 'react-router-dom';
import LogoMark from './LogoMark';

const links = [
  ['/', 'Home'], ['/assistant', 'Voice Assistant'], ['/pipeline', 'Live Pipeline'],
  ['/nlp', 'NLP Analyzer'], ['/models', 'Model Lab'], ['/training', 'Training'],
  ['/evaluation', 'Evaluation'], ['/alexa-vs-siri', 'Alexa vs Siri'],
  ['/india-challenges', 'India Challenges'], ['/research', 'Research'],
  ['/architecture', 'Architecture'], ['/about', 'About'],
];

export default function Nav() {
  return (
    <div className="navbar">
      <NavLink to="/" className="brand">
        <span className="brand-mark"><LogoMark size={32} /></span>
        <span className="brand-text">Bhasha<span className="accent">AI</span></span>
      </NavLink>
      <div className="nav-links">
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) => (isActive ? 'active' : '')}>
            {label}
          </NavLink>
        ))}
      </div>
    </div>
  );
}
