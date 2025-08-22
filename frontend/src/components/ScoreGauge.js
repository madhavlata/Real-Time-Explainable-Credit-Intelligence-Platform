import React from "react";

function ScoreGauge({ score }) {
  // Determine color based on score
  const getScoreColor = (s) => {
    if (s > 80) return "text-green-400";
    if (s > 60) return "text-yellow-400";
    return "text-red-400";
  };

  // Determine label based on score
  const getScoreLabel = (s) => {
    if (s > 80) return "Excellent";
    if (s > 60) return "Good";
    if (s > 40) return "Fair";
    return "Poor";
  };

  const scoreColor = getScoreColor(score);
  const scoreLabel = getScoreLabel(score);

  return (
    <div className="flex flex-col items-center justify-center h-full my-4">
      <div className={`text-8xl font-bold ${scoreColor}`}>
        {score.toFixed(2)}
      </div>
      <div className={`mt-2 text-xl font-semibold ${scoreColor}`}>
        {scoreLabel}
      </div>
      <div className="text-gray-400 mt-1">Out of 100</div>
    </div>
  );
}

export default ScoreGauge;
