import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function ScoreHistoryChart({ ticker }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const response = await axios.get(
          `${process.env.REACT_APP_API_URL}/scores/${ticker}`
        );
        const formattedData = response.data.map((item) => ({
          ...item,
          date: new Date(item.date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
        }));
        setHistory(formattedData.reverse());
      } catch (err) {
        console.error("Failed to fetch history:", err);
        setHistory([]);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [ticker]);

  if (loading) {
    return <div className="text-center p-10">Loading chart data...</div>;
  }

  if (history.length < 2) {
    return (
      <div className="text-center p-10 text-gray-400">
        Not enough historical data to plot a chart. At least two data points are
        required.
      </div>
    );
  }

  return (
    <div style={{ width: "100%", height: 300 }}>
      <ResponsiveContainer>
        <LineChart
          data={history}
          margin={{ top: 5, right: 20, left: -10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
          <XAxis dataKey="date" stroke="#A0AEC0" />
          {/* Update the Y-Axis domain for the new score range */}
          <YAxis domain={[300, 850]} stroke="#A0AEC0" />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1A202C",
              border: "1px solid #4A5568",
              borderRadius: "0.5rem",
            }}
            labelStyle={{ color: "#E2E8F0" }}
            itemStyle={{ color: "#63B3ED" }}
          />
          <Legend wrapperStyle={{ color: "#E2E8F0" }} />
          {/* --- THIS IS THE FIX --- */}
          {/* Update the dataKey from "score" to "creditworthiness" */}
          <Line
            type="monotone"
            dataKey="creditworthiness"
            name="Credit Score"
            stroke="#63B3ED"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ScoreHistoryChart;
