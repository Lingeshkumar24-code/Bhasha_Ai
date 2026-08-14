export default function LogoMark({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="50" r="46" stroke="url(#ringGrad)" strokeWidth="2.5" opacity="0.9" />
      <circle cx="50" cy="50" r="38" stroke="url(#ringGrad)" strokeWidth="1" opacity="0.4" />
      <path
        d="M40 20 C30 22 24 32 24 44 C24 54 28 60 34 66 L34 78 L44 70
           C48 71 52 71 56 70 C68 66 74 56 74 44 C74 30 60 18 44 19 Z"
        stroke="url(#faceGrad)" strokeWidth="1.6" fill="none" strokeLinejoin="round"
      />
      <g stroke="url(#faceGrad)" strokeWidth="1" opacity="0.85">
        <path d="M40 28 L46 28 L46 34 L52 34" fill="none" />
        <path d="M38 36 L44 36 L44 42" fill="none" />
        <circle cx="46" cy="34" r="1.4" fill="#FFD700" />
        <circle cx="44" cy="42" r="1.4" fill="#FFB703" />
        <path d="M40 46 L48 46 L48 52 L56 52" fill="none" />
        <circle cx="56" cy="52" r="1.4" fill="#FB8500" />
        <path d="M38 56 L44 56 L44 62" fill="none" />
        <circle cx="44" cy="62" r="1.4" fill="#FFD700" />
      </g>
      <g stroke="#FFB703" strokeLinecap="round">
        <line x1="60" y1="46" x2="60" y2="54" strokeWidth="2" />
        <line x1="65" y1="40" x2="65" y2="60" strokeWidth="2" />
        <line x1="70" y1="34" x2="70" y2="66" strokeWidth="2" />
        <line x1="75" y1="42" x2="75" y2="58" strokeWidth="2" />
        <line x1="80" y1="46" x2="80" y2="54" strokeWidth="2" />
      </g>
      <defs>
        <linearGradient id="ringGrad" x1="0" y1="0" x2="100" y2="100">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="100%" stopColor="#FB8500" />
        </linearGradient>
        <linearGradient id="faceGrad" x1="20" y1="20" x2="80" y2="80">
          <stop offset="0%" stopColor="#FFD700" />
          <stop offset="100%" stopColor="#FFB703" />
        </linearGradient>
      </defs>
    </svg>
  );
}
