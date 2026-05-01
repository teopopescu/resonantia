interface LogoProps {
  size?: number;
  className?: string;
}

export function ElabFTWLogo({ size = 24, className }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Flask body */}
      <path
        d="M18 6h12v14l10 18a4 4 0 01-3.5 6h-25A4 4 0 018 38L18 20V6z"
        fill="#E3F2FD"
        stroke="#0D47A1"
        strokeWidth="2.5"
        strokeLinejoin="round"
      />
      {/* Flask neck */}
      <path
        d="M18 6h12"
        stroke="#0D47A1"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      {/* Liquid level */}
      <path
        d="M13 32h22"
        stroke="#0D47A1"
        strokeWidth="1.5"
        strokeLinecap="round"
        opacity="0.4"
      />
      {/* "e" letter inside */}
      <text
        x="24"
        y="30"
        textAnchor="middle"
        dominantBaseline="central"
        fill="#0D47A1"
        fontFamily="sans-serif"
        fontWeight="700"
        fontSize="14"
      >
        e
      </text>
    </svg>
  );
}

export function BenchlingLogo({ size = 24, className }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* DNA helix - strand 1 */}
      <path
        d="M14 6C14 6 34 14 34 24C34 34 14 42 14 42"
        stroke="#4B6EF5"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* DNA helix - strand 2 */}
      <path
        d="M34 6C34 6 14 14 14 24C14 34 34 42 34 42"
        stroke="#4B6EF5"
        strokeWidth="2.5"
        strokeLinecap="round"
        fill="none"
      />
      {/* Cross rungs */}
      <line x1="18" y1="12" x2="30" y2="12" stroke="#4B6EF5" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      <line x1="15" y1="18" x2="33" y2="18" stroke="#4B6EF5" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      <line x1="14" y1="24" x2="34" y2="24" stroke="#4B6EF5" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      <line x1="15" y1="30" x2="33" y2="30" stroke="#4B6EF5" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      <line x1="18" y1="36" x2="30" y2="36" stroke="#4B6EF5" strokeWidth="1.5" strokeLinecap="round" opacity="0.5" />
      {/* Nodes at intersections */}
      <circle cx="14" cy="24" r="3" fill="#4B6EF5" />
      <circle cx="34" cy="24" r="3" fill="#4B6EF5" />
      <circle cx="24" cy="14" r="2.5" fill="#4B6EF5" opacity="0.7" />
      <circle cx="24" cy="34" r="2.5" fill="#4B6EF5" opacity="0.7" />
    </svg>
  );
}

export function DotmaticsLogo({ size = 24, className }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Connecting lines */}
      <line x1="12" y1="12" x2="24" y2="12" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="12" x2="36" y2="12" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="12" y1="12" x2="12" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="12" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="36" y1="12" x2="36" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="12" y1="24" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="24" x2="36" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="12" y1="24" x2="12" y2="36" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="24" x2="24" y2="36" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="36" y1="24" x2="36" y2="36" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="12" y1="36" x2="24" y2="36" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      <line x1="24" y1="36" x2="36" y2="36" stroke="#00897B" strokeWidth="1.5" opacity="0.3" />
      {/* Diagonal connections for molecule feel */}
      <line x1="12" y1="12" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.2" />
      <line x1="36" y1="12" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.2" />
      <line x1="12" y1="36" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.2" />
      <line x1="36" y1="36" x2="24" y2="24" stroke="#00897B" strokeWidth="1.5" opacity="0.2" />
      {/* Dot grid nodes */}
      <circle cx="12" cy="12" r="3.5" fill="#00897B" opacity="0.6" />
      <circle cx="24" cy="12" r="3" fill="#00897B" opacity="0.8" />
      <circle cx="36" cy="12" r="3.5" fill="#00897B" opacity="0.6" />
      <circle cx="12" cy="24" r="3" fill="#00897B" opacity="0.8" />
      <circle cx="24" cy="24" r="5" fill="#00897B" />
      <circle cx="36" cy="24" r="3" fill="#00897B" opacity="0.8" />
      <circle cx="12" cy="36" r="3.5" fill="#00897B" opacity="0.6" />
      <circle cx="24" cy="36" r="3" fill="#00897B" opacity="0.8" />
      <circle cx="36" cy="36" r="3.5" fill="#00897B" opacity="0.6" />
    </svg>
  );
}
