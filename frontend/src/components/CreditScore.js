import React from "react";

function CreditScore({ score }) {
  // Color scale for a 300-850 score range
  const getScoreColor = (s) => {
    if (s >= 800) return "text-green-400";
    if (s >= 740) return "text-green-500";
    if (s >= 670) return "text-yellow-400";
    if (s >= 580) return "text-orange-400";
    return "text-red-400";
  };

  const getScoreLabel = (s) => {
    if (s >= 800) return "Exceptional";
    if (s >= 740) return "Very Good";
    if (s >= 670) return "Good";
    if (s >= 580) return "Fair";
    return "Poor";
  };

  return (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg text-center">
      <h2 className="text-lg font-semibold text-gray-300 mb-2">
        Creditworthiness Score
      </h2>
      <div className={`text-7xl font-bold ${getScoreColor(score)}`}>
        {score.toFixed(0)}
      </div>
      <div className={`mt-2 text-xl font-semibold ${getScoreColor(score)}`}>
        {getScoreLabel(score)}
      </div>
      <p className="text-xs text-gray-500 mt-1">(Range: 300-850)</p>
    </div>
  );
}

export default CreditScore;
