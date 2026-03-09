import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/client";
import { ArrowLeft, Video, UploadCloud, Plus } from "lucide-react";

const ManageCourse = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  // New Video Form State
  const [formData, setFormData] = useState({
    title: "",
    duration: "", // Optional input for user or we can extract magically but let's keep it simple
    order: "",
  });
  const [videoFile, setVideoFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const [courseRes, videosRes] = await Promise.all([
          api.get(`courses/${id}/`),
          api.get("videos/"),
        ]);
        setCourse(courseRes.data);
        const courseVideos = videosRes.data.filter(
          (v) => v.course === parseInt(id),
        );
        setVideos(courseVideos.sort((a, b) => a.order - b.order));

        // Auto-suggest next order number
        if (courseVideos.length > 0) {
          setFormData((prev) => ({ ...prev, order: courseVideos.length + 1 }));
        } else {
          setFormData((prev) => ({ ...prev, order: 1 }));
        }
      } catch (err) {
        console.error("Failed to fetch data for management", err);
      } finally {
        setLoading(false);
      }
    };
    fetchCourseData();
  }, [id]);

  const handleInputChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setUploading(true);

    if (!videoFile) {
      setError("Please select a video file to upload.");
      setUploading(false);
      return;
    }

    try {
      const uploadData = new FormData();
      uploadData.append("course", id);
      uploadData.append("title", formData.title);
      uploadData.append("duration", formData.duration || 0); // Backend expects integer
      uploadData.append("order", formData.order || videos.length + 1);
      uploadData.append("video_file", videoFile);

      const response = await api.post("videos/", uploadData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setVideos([...videos, response.data].sort((a, b) => a.order - b.order));
      setSuccessMsg(`"${formData.title}" uploaded successfully!`);

      // Reset form
      setFormData({ title: "", duration: "", order: videos.length + 2 });
      setVideoFile(null);
      e.target.reset(); // Reset file input
    } catch (err) {
      console.error(err);
      setError(
        "Failed to upload video. Ensure it's a valid format and try again.",
      );
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
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

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}
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
        <ArrowLeft size={16} /> Back to Course
      </button>

      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>
          Manage Curriculum
        </h1>
        <p style={{ color: "var(--text-muted)" }}>
          Add, remove, and organize video lessons for{" "}
          <strong>{course?.title}</strong>.
        </p>
      </div>

      <div
        style={{
          display: "flex",
          gap: "2rem",
          flexWrap: "wrap",
          alignItems: "flex-start",
        }}
      >
        {/* Upload Form Block */}
        <div
          className="glass-panel"
          style={{ flex: "1 1 400px", padding: "2rem" }}
        >
          <h2
            style={{
              fontSize: "1.25rem",
              marginBottom: "1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <UploadCloud size={20} color="var(--accent-primary)" /> Upload New
            Lesson
          </h2>

          {error && (
            <div
              style={{
                color: "var(--error)",
                padding: "0.75rem",
                background: "rgba(239, 68, 68, 0.1)",
                borderRadius: "8px",
                marginBottom: "1rem",
              }}
            >
              {error}
            </div>
          )}
          {successMsg && (
            <div
              style={{
                color: "var(--success)",
                padding: "0.75rem",
                background: "var(--success-light)",
                borderRadius: "8px",
                marginBottom: "1rem",
              }}
            >
              {successMsg}
            </div>
          )}

          <form
            onSubmit={handleUpload}
            style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
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
                Lesson Title
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                required
                placeholder="e.g. Introduction to Variables"
              />
            </div>

            <div style={{ display: "flex", gap: "1rem" }}>
              <div style={{ flex: 1 }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontSize: "0.875rem",
                    fontWeight: "600",
                  }}
                >
                  Duration (mins)
                </label>
                <input
                  type="number"
                  name="duration"
                  value={formData.duration}
                  onChange={handleInputChange}
                  placeholder="e.g. 15"
                  required
                />
              </div>
              <div style={{ flex: 1 }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontSize: "0.875rem",
                    fontWeight: "600",
                  }}
                >
                  Order
                </label>
                <input
                  type="number"
                  name="order"
                  value={formData.order}
                  onChange={handleInputChange}
                  placeholder="e.g. 1"
                  required
                />
              </div>
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
                Video File
              </label>
              <input
                type="file"
                accept="video/mp4,video/x-m4v,video/*"
                onChange={handleFileChange}
                required
                style={{
                  background: "var(--bg-primary)",
                  border: "1px dashed var(--border-light)",
                  padding: "1rem",
                  width: "100%",
                  borderRadius: "8px",
                  cursor: "pointer",
                }}
              />
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={uploading}
              style={{
                marginTop: "0.5rem",
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              {uploading ? "Uploading..." : "Save Lesson"}
              {!uploading && <Plus size={18} />}
            </button>
          </form>
        </div>

        {/* Existing Lessons Block */}
        <div style={{ flex: "1 1 400px" }}>
          <h2
            style={{
              fontSize: "1.25rem",
              marginBottom: "1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Video size={20} color="var(--text-muted)" /> Current Lessons
          </h2>

          {videos.length === 0 ? (
            <div
              className="glass-panel"
              style={{ padding: "2rem", textAlign: "center" }}
            >
              <p style={{ color: "var(--text-muted)" }}>
                No lessons uploaded yet.
              </p>
            </div>
          ) : (
            <div
              style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
            >
              {videos.map((video) => (
                <div
                  key={video.id}
                  className="glass-panel"
                  style={{
                    padding: "1rem 1.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <h3 style={{ fontSize: "1rem", marginBottom: "0.25rem" }}>
                      {video.order}. {video.title}
                    </h3>
                    <span
                      style={{
                        fontSize: "0.875rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      {video.duration} mins
                    </span>
                  </div>
                  <button
                    className="btn-secondary"
                    style={{
                      padding: "0.5rem",
                      border: "none",
                      color: "var(--error)",
                    }}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ManageCourse;
