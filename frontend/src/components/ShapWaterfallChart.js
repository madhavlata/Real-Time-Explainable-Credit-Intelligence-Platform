import React, { useState } from "react";
import Plot from "react-plotly.js";

// Helper to format feature names for readability
const formatFeatureName = (name) => {
  return name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
};

// Helper to process SHAP data for the waterfall chart
const processShapData = (shapData) => {
  if (!shapData || !shapData.shap_values || !shapData.feature_values) {
    return { x: [], y: [], text: [], measure: [] };
  }

  const baseValue = shapData.base_value;
  const shapValues = shapData.shap_values;

  let cumulative = baseValue;
  const xData = ["Base Value"];
  const yData = [baseValue];
  const measure = ["absolute"];

  // Sort features by the magnitude of their SHAP value for better visualization
  const sortedFeatures = Object.keys(shapValues).sort(
    (a, b) => Math.abs(shapValues[b]) - Math.abs(shapValues[a])
  );

  for (const feature of sortedFeatures) {
    const shapValue = shapValues[feature];
    xData.push(formatFeatureName(feature));
    yData.push(shapValue);
    measure.push("relative");
    cumulative += shapValue;
  }

  xData.push("Final Prediction");
  yData.push(cumulative);
  measure.push("total");

  return {
    x: xData,
    y: yData,
    text: yData.map((val) => val.toFixed(4)),
    measure: measure,
  };
};

function ShapWaterfallChart({ explanations }) {
  const [activeTab, setActiveTab] = useState("label_60d");

  const chartData = processShapData(explanations[activeTab]);

  const tabs = [
    { key: "label_5d", name: "Near-Term (5d)" },
    { key: "label_20d", name: "Mid-Term (20d)" },
    { key: "label_60d", name: "Long-Term (60d)" },
  ];

  return (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg h-full">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-200">
          Model Explainability (SHAP)
        </h2>
        <div className="flex space-x-1 bg-gray-700 p-1 rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                activeTab === tab.key
                  ? "bg-cyan-600 text-white"
                  : "text-gray-300 hover:bg-gray-600"
              }`}
            >
              {tab.name}
            </button>
          ))}
        </div>
      </div>

      <Plot
        data={[
          {
            type: "waterfall",
            x: chartData.x,
            y: chartData.y,
            measure: chartData.measure,
            text: chartData.text,
            textposition: "outside",
            connector: { line: { color: "rgb(100, 100, 100)" } },
            increasing: { marker: { color: "#EF4444" } }, // Red for increasing risk
            decreasing: { marker: { color: "#22C55E" } }, // Green for decreasing risk
            totals: { marker: { color: "#38BDF8" } }, // Blue for base/total
          },
        ]}
        layout={{
          plot_bgcolor: "rgba(0,0,0,0)",
          paper_bgcolor: "rgba(0,0,0,0)",
          font: { color: "#A0AEC0" },
          xaxis: { autorange: true, showgrid: false },
          yaxis: { autorange: true, gridcolor: "#4A5568" },
          margin: { l: 40, r: 20, t: 20, b: 120 }, // Adjust bottom margin for labels
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: "100%", height: "calc(100% - 50px)" }}
      />
    </div>
  );
}

export default ShapWaterfallChart;
