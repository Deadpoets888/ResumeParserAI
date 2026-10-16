import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./index.css";

function SearchPage() {
  const [userPrompt, setUserPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSearch = async () => {
    if (!userPrompt.trim()) return;
    setLoading(true);
    setError("");
    try {
      const apiUrl = process.env.REACT_APP_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/search-resume/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_prompt: userPrompt }),
      });
      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || "An error occurred while searching.");
        return;
      }
      if (data.message) {
        // API returned a "no match" message
        setError(data.message);
        return;
      }
      navigate("/search-result", { state: { resume: data } });
    } catch (err) {
      console.error("Error searching resume:", err);
      setError("Failed to connect to the server. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <h2>Search Resume</h2>
      <input
        type="text"
        placeholder="Enter search prompt"
        value={userPrompt}
        onChange={(e) => setUserPrompt(e.target.value)}
        className="search-input"
      />
      {error && <p style={{ color: "red", marginTop: "10px" }}>{error}</p>}
      <button onClick={handleSearch} className="search-button" disabled={loading}>
        {loading ? "We are processing. Plz wait" : "Search"}
      </button>
    </div>
  );
}

export default SearchPage;