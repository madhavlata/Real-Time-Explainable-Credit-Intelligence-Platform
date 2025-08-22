import React, { useState, useEffect } from "react";
import axios from "axios";
import ScoreGauge from "./ScoreGauge";
import FeaturesTable from "./FeaturesTable";
import ScoreHistoryChart from "./ScoreHistoryChart";

function Dashboard({ ticker }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ticker) return;

    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        // IMPORTANT: Replace with your actual backend URL
        const response = await axios.get(
          `https://real-time-explainable-credit.onrender.com/scores/${ticker}`
        );
        setData(response.data);
      } catch (err) {
        setError(
          `Failed to fetch data for ${ticker}. Please check the ticker and try again.`
        );
        setData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker]); // Re-run this effect ONLY when the ticker changes

  if (loading) {
    return (
      <div className="text-center mt-20 text-gray-400">
        <p>Loading data for ${ticker}...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center mt-20 text-red-400 bg-red-900/20 p-6 rounded-lg">
        <p>{error}</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Main Score Section */}
      <div className="lg:col-span-1 bg-gray-800 p-6 rounded-xl shadow-lg flex flex-col justify-between">
        <div>
          <h2 className="text-2xl font-semibold mb-4 text-gray-200">
            {data.ticker} Credit Score
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Last updated: {new Date(data.date).toLocaleDateString()}
          </p>
        </div>
        <ScoreGauge score={data.score} />
      </div>

      {/* Financial Features Table */}
      <div className="lg:col-span-2 bg-gray-800 p-6 rounded-xl shadow-lg">
        <h2 className="text-2xl font-semibold mb-4 text-gray-200">
          Key Financial Features
        </h2>
        <FeaturesTable features={data.features} />
      </div>

      {/* Historical Chart */}
      <div className="lg:col-span-3 bg-gray-800 p-6 rounded-xl shadow-lg">
        <h2 className="text-2xl font-semibold mb-4 text-gray-200">
          Score History
        </h2>
        <ScoreHistoryChart ticker={ticker} />
      </div>
    </div>
  );
}

export default Dashboard;
