import React from "react";

function SentimentGauge({ sentiment }) {
  // --- THIS IS THE FIX ---
  // Scale the sentiment (assuming a range like -1 to +1) to a -50 to +50 display range.
  const scaledValue = sentiment * 50;

  const getBarColor = (s) => {
    if (s > 15) return "bg-green-500";
    if (s < -15) return "bg-red-500";
    return "bg-yellow-500";
  };

  // Clamp the bar width between 0 and 50 for the visual display
  const barMagnitude = Math.min(Math.abs(scaledValue), 50);
  const barWidth = barMagnitude * 2; // Scale to percentage for tailwind width
  const barOffset = scaledValue > 0 ? "50%" : `${50 - barMagnitude}%`;

  return (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
      <h2 className="text-lg font-semibold text-gray-300 mb-4 text-center">
        MEDIA MOMENTUM INDEX
      </h2>
      <div className="relative w-full h-4 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`absolute h-4 rounded-full ${getBarColor(scaledValue)}`}
          style={{
            width: `${barWidth}%`,
            left: barOffset,
          }}
        ></div>
        {/* Center Line */}
        <div className="absolute top-0 left-1/2 w-0.5 h-4 bg-gray-500"></div>
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-2">
        <span>Negative</span>
        <span>Neutral</span>
        <span>Positive</span>
      </div>
      {/* Display the clamped value visually but the true value in text */}
      <p className="text-center text-2xl font-bold mt-3">
        {scaledValue.toFixed(1)}
      </p>
    </div>
  );
}

export default SentimentGauge;
