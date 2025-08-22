import React from "react";

// A helper component for each risk item
const RiskItem = ({ label, value }) => {
  const riskPercent = value * 100;
  const getColor = (p) => {
    if (p < 10) return "bg-green-500";
    if (p < 40) return "bg-yellow-500";
    return "bg-red-500";
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-300">{label}</span>
        <span className="text-sm font-bold text-white">
          {riskPercent.toFixed(2)}%
        </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full ${getColor(riskPercent)}`}
          style={{ width: `${riskPercent}%` }}
        ></div>
      </div>
    </div>
  );
};

function RiskProbabilities({ risks }) {
  return (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
      <h2 className="text-lg font-semibold text-gray-300 mb-4">
        Default Risk Horizon
      </h2>
      <div className="space-y-4">
        <RiskItem label="Near-Term (5 Day)" value={risks.label_5d} />
        <RiskItem label="Mid-Term (20 Day)" value={risks.label_20d} />
        <RiskItem label="Long-Term (60 Day)" value={risks.label_60d} />
      </div>
    </div>
  );
}

export default RiskProbabilities;
