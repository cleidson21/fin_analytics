"use client";

interface DiversificationGaugeProps {
  score: number; // 0 to 100
}

function getScoreColor(score: number): string {
  if (score >= 66) return "#4ecf98"; // Diversificado
  if (score >= 41) return "#f5a623"; // Moderado
  return "#e97070"; // Concentrado
}

export function DiversificationGauge({ score }: DiversificationGaugeProps) {
  const color = getScoreColor(score);

  // SVG parameters
  const radius = 40;
  const circumference = Math.PI * radius;
  // Calculate how much to "hide" of the stroke
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex flex-col items-center justify-end" style={{ width: 80, height: 48 }}>
      <svg viewBox="0 0 100 50" className="w-full h-full overflow-visible">
        {/* Background Arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Foreground Arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
        />
      </svg>

      {/* Label central fixo e alinhado ao centro geométrico */}
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center justify-end" style={{ paddingBottom: "2px" }}>
        <span
          className="text-[22px] font-bold leading-none tracking-tight"
          style={{ color, textShadow: `0 2px 10px ${color}40` }}
        >
          {score}
        </span>
      </div>
    </div>
  );
}
