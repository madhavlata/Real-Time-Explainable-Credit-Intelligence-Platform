import React, { useState } from "react";
import SearchBar from "./components/SearchBar";
import Dashboard from "./components/Dashboard";

function App() {
  const [ticker, setTicker] = useState("AAPL"); // Set a default ticker

  const handleSearch = (searchTicker) => {
    // Prevent empty searches
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

        <SearchBar onSearch={handleSearch} initialValue={ticker} />

        {ticker && <Dashboard key={ticker} ticker={ticker} />}
      </div>
    </div>
  );
}

export default App;
