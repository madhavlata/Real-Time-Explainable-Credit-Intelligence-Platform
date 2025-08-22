import React, { useState } from "react";

function SearchBar({ onSearch, initialValue }) {
  const [inputValue, setInputValue] = useState(initialValue);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(inputValue);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Enter a stock ticker (e.g., GOOGL)"
        className="w-full max-w-sm p-3 bg-gray-700 text-white border-2 border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
      />
      <button
        type="submit"
        className="px-6 py-3 bg-cyan-600 text-white font-semibold rounded-lg hover:bg-cyan-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-opacity-50 transition-colors"
      >
        Search
      </button>
    </form>
  );
}

export default SearchBar;
