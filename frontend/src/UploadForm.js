import { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";

function UploadForm() {
  const [file, setFile] = useState(null);
  const [modelType, setModelType] = useState("gpt_fitz");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => setFile(e.target.files[0]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return alert("Please upload a PDF");
    const formData = new FormData();
    formData.append("model_type", modelType);
    formData.append("file", file);

    setLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL || "http://localhost:8000";
      await axios.post(`${apiUrl}/api/v1/resume/`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      navigate("/thank-you"); // Redirect to thank you page
    } catch (error) {
      console.error("Upload failed:", error);
      alert("Upload failed. Try again.");
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="container">
      <h2>Upload Resume</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept="application/pdf" onChange={handleFileChange} required />
        <label>
          <input
            type="radio"
            value="Gpt+fitz"
            checked={modelType === "gpt_fitz"}
            onChange={() => setModelType("gpt_fitz")}
          />
          GPT+Fitz
        </label>
        <label>
          <input
            type="radio"
            value="Mistral"
            checked={modelType === "mistral"}
            onChange={() => setModelType("mistral")}
          />
          Mistral
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Uploading..." : "Submit"}
        </button>
      </form>
    </div>
  );
}

export default UploadForm;
