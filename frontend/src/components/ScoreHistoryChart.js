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
        // IMPORTANT: Replace with your actual history endpoint
        const response = await axios.get(
          `http://localhost:5000/api/history/${ticker}`
        );
        // Format date for better chart readability
        const formattedData = response.data.map((item) => ({
          ...item,
          date: new Date(item.date).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          }),
        }));
        setHistory(formattedData);
      } catch (err) {
        console.error("Failed to fetch history:", err);
        setHistory([]); // Clear data on error
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [ticker]);

  if (loading) {
    return <div className="text-center p-10">Loading chart data...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="text-center p-10">
        No historical data available for this ticker.
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
          <YAxis domain={[0, 100]} stroke="#A0AEC0" />
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
          <Line
            type="monotone"
            dataKey="score"
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
