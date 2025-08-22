import React from "react";

// A helper to format the feature keys into human-readable labels
const formatKey = (key) => {
  return key
    .replace(/_/g, " ")
    .replace(/([A-Z])/g, " $1") // Add space before capital letters
    .replace(/\b\d+\w*/, (match) => match.toUpperCase()) // Uppercase d in 5d, 20d
    .replace(/^./, (str) => str.toUpperCase()); // Capitalize first letter
};

function FeaturesTable({ features }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-700">
        <tbody className="bg-gray-800 divide-y divide-gray-700">
          {Object.entries(features).map(([key, value]) => (
            <tr key={key} className="hover:bg-gray-700/50">
              <td className="px-6 py-4 text-sm font-medium text-gray-300 whitespace-nowrap">
                {formatKey(key)}
              </td>
              <td className="px-6 py-4 text-sm text-white whitespace-nowrap font-mono text-right">
                {typeof value === "number" ? value.toFixed(4) : value}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default FeaturesTable;
