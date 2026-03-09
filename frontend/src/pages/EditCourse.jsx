import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/client";
import { ArrowLeft, Save, Image as ImageIcon } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const EditCourse = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [formData, setFormData] = useState({
    title: "",
    description: "",
  });
  const [thumbnail, setThumbnail] = useState(null);
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchCourse = async () => {
      try {
        const response = await api.get(`courses/${id}/`);

        // Ensure user is the instructor
        if (response.data.instructor !== user?.id) {
          setError("You do not have permission to edit this course.");
          setIsLoading(false);
          return;
        }

        setFormData({
          title: response.data.title,
          description: response.data.description,
        });
        setPreview(response.data.thumbnail);
        setIsLoading(false);
      } catch (err) {
        console.error("Failed to load course details", err);
        setError("Could not load course.");
        setIsLoading(false);
      }
    };

    if (user) {
      fetchCourse();
    }
  }, [id, user]);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setThumbnail(file);

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
    setIsSaving(true);

    try {
      const data = new FormData();
      data.append("title", formData.title);
      data.append("description", formData.description);
      if (thumbnail) {
        data.append("thumbnail", thumbnail);
      }

      await api.patch(`courses/${id}/`, data, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      navigate(`/course/${id}`);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail ||
          "Failed to update course. Please try again.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div
        style={{ display: "flex", justifyContent: "center", padding: "4rem" }}
      >
        <div
          style={{
            width: "40px",
            height: "40px",
            border: "3px solid rgba(249, 115, 22, 0.2)",
            borderTopColor: "var(--accent-primary)",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        />
      </div>
    );
  }

  if (error && !formData.title) {
    return (
      <div
        style={{ padding: "4rem", textAlign: "center", color: "var(--error)" }}
      >
        <h2>{error}</h2>
        <button
          onClick={() => navigate("/dashboard")}
          className="btn-secondary"
          style={{ marginTop: "1rem" }}
        >
          Go to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}
    >
      <button
        onClick={() => navigate(`/course/${id}`)}
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
        Back to Course
      </button>

      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>
          Edit Course
        </h1>
        <p style={{ color: "var(--text-muted)" }}>
          Update the details of your course.
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
            Course Cover Image (Optional)
          </label>
          <p
            style={{
              fontSize: "0.75rem",
              color: "var(--text-muted)",
              marginBottom: "0.5rem",
            }}
          >
            Leave empty to keep the current image.
          </p>
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
                    Click or drag a new image to upload
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
            disabled={isSaving}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              padding: "0.75rem 2rem",
            }}
          >
            {isSaving ? "Saving..." : "Save Changes"}
            {!isSaving && <Save size={18} />}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditCourse;
