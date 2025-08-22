import React, { useState } from "react";
import SearchBar from "./components/SearchBar";
import Dashboard from "./components/Dashboard";

// Helper function to get today's date in YYYY-MM-DD format
const getTodayString = () => {
  return new Date().toISOString().split("T")[0];
};

function App() {
  const [ticker, setTicker] = useState("AAPL");
  // 1. Add state for the selected date, defaulting to today
  const [date, setDate] = useState(getTodayString());

  const handleSearch = (searchTicker) => {
    if (searchTicker) {
      setTicker(searchTicker.toUpperCase());
    }
  };

  return (
    <div className="bg-gray-900 min-h-screen text-white font-sans p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-cyan-400 tracking-tight">
            Creditworthiness Rating Platform
          </h1>
          <p className="text-gray-400 mt-1">
            Real-time financial health analysis.
          </p>
        </header>

        {/* 2. Add a container for the inputs */}
        <div className="flex flex-wrap items-center gap-4 mb-8">
          <SearchBar onSearch={handleSearch} initialValue={ticker} />
          <div className="flex items-center gap-2">
            <label htmlFor="date-picker" className="font-medium text-gray-300">
              Date:
            </label>
            <input
              id="date-picker"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              max={getTodayString()} // Prevent selecting future dates
              className="p-3 bg-gray-700 text-white border-2 border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
            />
          </div>
        </div>

        {/* 3. Pass both ticker and date down to the Dashboard */}
        {ticker && date && (
          <Dashboard key={`${ticker}-${date}`} ticker={ticker} date={date} />
        )}
      </div>
    </div>
  );
}

export default App;
