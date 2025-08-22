import React, { useState, useEffect } from "react";
import axios from "axios";
import CreditScore from "./CreditScore";
import RiskProbabilities from "./RiskProbabilities";
import SentimentGauge from "./SentimentGauge";
import ShapWaterfallChart from "./ShapWaterfallChart";
// 1. Import the ScoreHistoryChart component
import ScoreHistoryChart from "./ScoreHistoryChart";

function Dashboard({ ticker, date }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadingMessage, setLoadingMessage] = useState(
    `Loading data for ${ticker}...`
  );

  useEffect(() => {
    setData(null);
    setLoading(true);
    setError("");
    setLoadingMessage(`Loading data for ${ticker} on ${date}...`);

    const timer = setTimeout(() => {
      setLoadingMessage(
        `This is a new ticker. Please wait while we perform the analysis (this may take up to 30 seconds)...`
      );
    }, 3000);

    const fetchData = async () => {
      try {
        const response = await axios.get(
          `${process.env.REACT_APP_API_URL}/scores/${ticker}/${date}`
        );
        setData(response.data);
      } catch (err) {
        const detail =
          err.response?.data?.detail ||
          "Please check the ticker and try again.";
        setError(`Failed to fetch data for ${ticker} on ${date}. ${detail}`);
      } finally {
        setLoading(false);
        clearTimeout(timer);
      }
    };

    fetchData();

    return () => clearTimeout(timer);
  }, [ticker, date]);

  if (loading) {
    return (
      <div className="text-center mt-20 text-yellow-300">
        <p>{loadingMessage}</p>
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
    // Use a flex column layout for the whole dashboard area
    <div className="flex flex-col gap-6 mt-8">
      {/* Top row with the main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {/* Left Column: Key Metrics */}
        <div className="lg:col-span-1 xl:col-span-1 flex flex-col gap-6">
          <CreditScore score={data.creditworthiness} />
          <RiskProbabilities risks={data.risk_probs} />
          <SentimentGauge sentiment={data.features.decayed_sentiment} />
        </div>

        {/* Right Column: Explainability */}
        <div className="lg:col-span-2 xl:col-span-3">
          <ShapWaterfallChart explanations={data.shap_explanations} />
        </div>
      </div>

      {/* 2. Add the ScoreHistoryChart in a new full-width row */}
      <div className="bg-gray-800 p-6 rounded-xl shadow-lg">
        <h2 className="text-xl font-semibold mb-4 text-gray-200">
          Score History
        </h2>
        <ScoreHistoryChart ticker={ticker} />
      </div>
    </div>
  );
}

export default Dashboard;
