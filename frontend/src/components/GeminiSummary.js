import React, { useState, useEffect } from "react";
import { Sparkles } from "lucide-react";

// The URL for the Gemini API
const GEMINI_API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=AIzaSyAR28y86PuAVJtOXr9pVA8hVh2DMELgU74`;
const GeminiSummary = ({ ticker, creditworthiness, shapExplanations }) => {
  const [summary, setSummary] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!ticker || !creditworthiness || !shapExplanations) {
      return;
    }

    const generateSummary = async () => {
      setIsLoading(true);
      setError("");
      setSummary("");

      try {
        // --- 1. Prepare the data and prompt ---
        const shapInfo = shapExplanations?.label_20d || {};
        const shapValues = shapInfo.shap_values || {};

        const sortedFeatures = Object.entries(shapValues).sort(
          (a, b) => Math.abs(b[1]) - Math.abs(a[1])
        );

        const positiveFactors = sortedFeatures
          .filter(([, v]) => v > 0)
          .slice(0, 3)
          .map(([f]) => f);
        const negativeFactors = sortedFeatures
          .filter(([, v]) => v < 0)
          .slice(0, 3)
          .map(([f]) => f);

        const prompt = `
          Analyze the following financial data for the company with ticker symbol ${ticker} to explain its credit score.
          The current creditworthiness score is ${creditworthiness.toFixed(
            2
          )} (out of 850, where higher is better).

          The primary factors INCREASING the credit risk (bad for the score) are: ${
            positiveFactors.join(", ") || "None"
          }.
          The primary factors DECREASING the credit risk (good for the score) are: ${
            negativeFactors.join(", ") || "None"
          }.

          Based on this, generate a concise, two-line summary in plain language for a non-technical stakeholder, explaining why the credit score is what it is.
        `;

        // --- 2. Make the API call to Gemini ---
        const response = await fetch(GEMINI_API_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }],
          }),
        });

        if (!response.ok) {
          throw new Error(`API call failed with status: ${response.status}`);
        }

        const data = await response.json();

        const generatedText = data.candidates?.[0]?.content?.parts?.[0]?.text;

        if (generatedText) {
          setSummary(generatedText.trim().replace(/\n/g, " "));
        } else {
          throw new Error("Invalid response structure from Gemini API.");
        }
      } catch (err) {
        console.error("Error generating Gemini summary:", err);
        setError("An automated summary is currently unavailable.");
      } finally {
        setIsLoading(false);
      }
    };

    generateSummary();
  }, [ticker, creditworthiness, shapExplanations]); // Re-run when data changes

  return (
    <div className="bg-gray-800/50 p-6 rounded-2xl border border-gray-700/50">
      <h3 className="flex items-center text-lg font-semibold text-white mb-3">
        <Sparkles className="h-5 w-5 text-yellow-400 mr-2" />
        AI-Powered Summary
      </h3>
      {isLoading && (
        <p className="text-gray-400 animate-pulse">Generating summary...</p>
      )}
      {error && <p className="text-red-500">{error}</p>}
      {summary && <p className="text-gray-300 leading-relaxed">{summary}</p>}
    </div>
  );
};

export default GeminiSummary;
