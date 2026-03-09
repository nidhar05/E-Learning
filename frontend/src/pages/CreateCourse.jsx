import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { PlusCircle, Image as ImageIcon, ArrowLeft } from "lucide-react";

const CreateCourse = () => {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });
  const [thumbnail, setThumbnail] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate();

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setThumbnail(file);

      // Create local preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const data = new FormData();
      data.append("title", formData.title);
      data.append("description", formData.description);
      if (thumbnail) {
        data.append("thumbnail", thumbnail);
      }

      await api.post("courses/create/", data, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          (typeof err.response?.data === "object"
            ? Object.values(err.response.data).flat().join(" ")
            : "Failed to create course. Please try again."),
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}
    >
      <button
        onClick={() => navigate("/dashboard")}
        style={{
          background: "none",
          border: "none",
          color: "var(--text-muted)",
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          cursor: "pointer",
          marginBottom: "2rem",
          fontSize: "0.875rem",
        }}
      >
        <ArrowLeft size={16} />
        Back to Dashboard
      </button>

      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>
          Create New Course
        </h1>
        <p style={{ color: "var(--text-muted)" }}>
          Fill in the details to publish a new course to the platform.
        </p>
      </div>

      {error && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.1)",
            color: "var(--error)",
            padding: "1rem",
            borderRadius: "8px",
            marginBottom: "1.5rem",
            border: "1px solid rgba(239, 68, 68, 0.2)",
          }}
        >
          {error}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="glass-panel"
        style={{
          padding: "2.5rem",
          display: "flex",
          flexDirection: "column",
          gap: "1.5rem",
        }}
      >
        <div>
          <label
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontSize: "0.875rem",
              fontWeight: "600",
            }}
          >
            Course Title
          </label>
          <input
            type="text"
            name="title"
            placeholder="e.g. Advanced React Patterns"
            value={formData.title}
            onChange={handleInputChange}
            required
            style={{ fontSize: "1.125rem", padding: "1rem" }}
          />
        </div>

        <div>
          <label
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontSize: "0.875rem",
              fontWeight: "600",
            }}
          >
            Course Description
          </label>
          <textarea
            name="description"
            placeholder="Describe what students will learn in this course..."
            value={formData.description}
            onChange={handleInputChange}
            required
            rows="5"
            style={{ resize: "vertical" }}
          />
        </div>

        <div>
          <label
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontSize: "0.875rem",
              fontWeight: "600",
            }}
          >
            Course Cover Image
          </label>

          <div
            style={{
              border: "2px dashed var(--border-light)",
              borderRadius: "12px",
              padding: "2rem",
              textAlign: "center",
              position: "relative",
              background: "var(--bg-primary)",
              transition: "all 0.2s",
              overflow: "hidden",
            }}
          >
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                opacity: 0,
                cursor: "pointer",
                zIndex: 10,
              }}
            />
            {preview ? (
              <img
                src={preview}
                alt="Course preview"
                style={{
                  width: "100%",
                  height: "200px",
                  objectFit: "cover",
                  borderRadius: "8px",
                }}
              />
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "1rem",
                }}
              >
                <ImageIcon
                  size={48}
                  color="var(--accent-primary)"
                  style={{ opacity: 0.8 }}
                />
                <div>
                  <p style={{ fontWeight: "600" }}>
                    Click or drag image to upload
                  </p>
                  <p
                    style={{
                      fontSize: "0.875rem",
                      color: "var(--text-muted)",
                      marginTop: "0.25rem",
                    }}
                  >
                    SVG, PNG, JPG or GIF (max. 800x400px)
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div
          style={{
            marginTop: "1rem",
            paddingTop: "1.5rem",
            borderTop: "1px solid var(--border-light)",
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 2rem",
            }}
          >
            {isLoading ? "Publishing..." : "Publish Course"}
            {!isLoading && <PlusCircle size={18} />}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateCourse;
