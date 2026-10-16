import { useLocation } from "react-router-dom";
import "./index.css";

function SearchResult() {
  const location = useLocation();
  const resume = location.state?.resume;

  return (
    <div className="result-container">
      <h2>Resume Details</h2>
      {resume ? (
        <div className="resume-details">
          <p><strong>Name:</strong> {resume.name}</p>
          <p><strong>Email:</strong> {resume.email}</p>
          <p><strong>Phone:</strong> {resume.phone_number || "N/A"}</p>

          {/* Skills Section */}
          <h3>Skills</h3>
          {resume.skills && Object.keys(resume.skills).length > 0 ? (
            <ul>
              {Object.entries(resume.skills).map(([category, items]) => (
                <li key={category}>
                  <strong>{category}:</strong> {Array.isArray(items) ? items.join(", ") : items}
                </li>
              ))}
            </ul>
          ) : (
            <p>N/A</p>
          )}

          {/* Work Experience Section */}
          <h3>Work Experience</h3>
          {resume.work_experience && resume.work_experience.length > 0 ? (
            <ul>
              {resume.work_experience.map((exp, index) => (
                <li key={index}>
                  {Object.entries(exp).map(([key, value]) => (
                    <p key={key}><strong>{key}:</strong> {value}</p>
                  ))}
                </li>
              ))}
            </ul>
          ) : (
            <p>N/A</p>
          )}

          {/* Education Section */}
          <h3>Education</h3>
          {resume.education && resume.education.length > 0 ? (
            <ul>
              {resume.education.map((edu, index) => (
                <li key={index}>
                  {Object.entries(edu).map(([key, value]) => (
                    <p key={key}><strong>{key}:</strong> {value}</p>
                  ))}
                </li>
              ))}
            </ul>
          ) : (
            <p>N/A</p>
          )}

          {/* Certifications Section */}
          <h3>Certifications</h3>
          {resume.certifications && resume.certifications.length > 0 ? (
            <ul>
              {resume.certifications.map((cert, index) => (
                <li key={index}>
                  {typeof cert === "string"
                    ? cert
                    : Object.entries(cert).map(([key, value]) => (
                        <p key={key}><strong>{key}:</strong> {String(value)}</p>
                      ))}
                </li>
              ))}
            </ul>
          ) : (
            <p>N/A</p>
          )}

          {/* Projects Section */}
          <h3>Projects</h3>
          {resume.projects && resume.projects.length > 0 ? (
            <ul>
              {resume.projects.map((project, index) => (
                <li key={index}>
                    {Object.entries(project).map(([key, value]) => (
                    <p key={key}><strong>{key}:</strong> {value}</p>
                  ))}
                </li>
              ))}
            </ul>
          ) : (
            <p>N/A</p>
          )}

          <p><strong>GPA:</strong> {resume.gpa || "N/A"}</p>
          <p><strong>Model Type:</strong> {resume.model_type}</p>
        </div>
      ) : (
        <p>No resume data found.</p>
      )}
    </div>
  );
}

export default SearchResult;
