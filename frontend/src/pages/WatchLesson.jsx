import React, { useState, useEffect } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import {
  ArrowLeft,
  CheckCircle,
  PlayCircle,
  Trophy,
  LayoutDashboard,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const WatchLesson = () => {
  const { id, videoId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [courseProgress, setCourseProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProgress = async () => {
    try {
      if (user?.role === "student") {
        const res = await api.get(`progress/${id}/`);
        setCourseProgress(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch progress", err);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [courseRes, videosRes] = await Promise.all([
          api.get(`courses/${id}/`),
          api.get("videos/"),
        ]);
        setCourse(courseRes.data);

        const courseVideos = videosRes.data
          .filter((v) => v.course === parseInt(id))
          .sort((a, b) => a.order - b.order);
        setVideos(courseVideos);

        const activeVideo = courseVideos.find(
          (v) => v.id === parseInt(videoId),
        );
        setCurrentVideo(activeVideo || courseVideos[0]); // Fallback to first video

        await fetchProgress();
      } catch (err) {
        console.error("Failed to load lesson", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, videoId, user]);

  const handleVideoEnded = async () => {
    if (user?.role !== "student" || !currentVideo) return;

    try {
      await api.post(`progress/complete/${currentVideo.id}/`);
      await fetchProgress(); // Refresh the progress bar
    } catch (err) {
      console.error("Failed to mark complete", err);
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
            border: "3px solid rgba(16, 185, 129, 0.2)",
            borderTopColor: "var(--success)",
            borderRadius: "50%",
            animation: "spin 1s linear infinite",
          }}
        />
      </div>
    );
  }

  if (!currentVideo) {
    return (
      <div style={{ padding: "4rem", textAlign: "center" }}>
        <h2>Video not found</h2>
        <button
          onClick={() => navigate(`/course/${id}`)}
          className="btn-secondary"
          style={{ marginTop: "1rem" }}
        >
          Back to Course
        </button>
      </div>
    );
  }

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "1600px", margin: "0 auto" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
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
            fontSize: "0.875rem",
          }}
        >
          <ArrowLeft size={16} /> Back to Course Overview
        </button>

        {courseProgress && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              background: "#f8fafc",
              padding: "0.5rem 1rem",
              borderRadius: "999px",
              border: "1px solid var(--border-light)",
            }}
          >
            <Trophy size={18} color="var(--accent-primary)" />
            <div style={{ fontSize: "0.875rem", fontWeight: "600" }}>
              Course Progress: {courseProgress.progress_percentage.toFixed(0)}%
            </div>
            <div
              style={{
                width: "100px",
                height: "6px",
                background: "rgba(15, 23, 42, 0.1)",
                borderRadius: "999px",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${courseProgress.progress_percentage}%`,
                  height: "100%",
                  background: "var(--success)",
                  transition: "width 0.5s ease",
                }}
              />
            </div>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
        {/* Main Video Player Area */}
        <div
          style={{
            flex: "3 1 800px",
            display: "flex",
            flexDirection: "column",
            gap: "1.5rem",
          }}
        >
          <div
            className="glass-panel"
            style={{
              overflow: "hidden",
              padding: 0,
              background: "#000",
              borderRadius: "12px",
              boxShadow:
                "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
            }}
          >
            <video
              key={currentVideo.id} // Force re-render when video changes
              controls
              autoPlay
              onEnded={handleVideoEnded}
              style={{ width: "100%", aspectRatio: "16/9", outline: "none" }}
              src={currentVideo.video_file}
            >
              Your browser does not support the video tag.
            </video>
          </div>

          <div className="glass-panel" style={{ padding: "2rem" }}>
            <h1 style={{ fontSize: "1.75rem", marginBottom: "0.5rem" }}>
              {currentVideo.order}. {currentVideo.title}
            </h1>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
              Course: <strong>{course?.title}</strong>
            </p>

            <div
              style={{
                padding: "1rem",
                background: "rgba(249, 115, 22, 0.05)",
                borderRadius: "8px",
                border: "1px solid rgba(249, 115, 22, 0.1)",
              }}
            >
              <h3
                style={{
                  fontSize: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  color: "var(--accent-hover)",
                }}
              >
                <CheckCircle size={18} /> Instructor Notes
              </h3>
              <p
                style={{
                  fontSize: "0.875rem",
                  marginTop: "0.5rem",
                  lineHeight: "1.6",
                }}
              >
                Ensure you watch the video entirely to automatically mark it as
                completed and update your course progress. Feel free to use the
                comments section below for any questions!
              </p>
            </div>
          </div>
        </div>

        {/* Curriculum Sidebar */}
        <div style={{ flex: "1 1 300px" }}>
          <div
            className="glass-panel"
            style={{
              position: "sticky",
              top: "100px",
              maxHeight: "calc(100vh - 120px)",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                padding: "1.5rem",
                borderBottom: "1px solid var(--border-light)",
              }}
            >
              <h2
                style={{
                  fontSize: "1.25rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <LayoutDashboard size={20} color="var(--accent-primary)" />{" "}
                Curriculum
              </h2>
            </div>

            <div style={{ display: "flex", flexDirection: "column" }}>
              {videos.map((video) => (
                <Link
                  key={video.id}
                  to={`/course/${id}/watch/${video.id}`}
                  style={{
                    padding: "1rem 1.5rem",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    textDecoration: "none",
                    color: "inherit",
                    borderBottom: "1px solid var(--border-light)",
                    background:
                      currentVideo.id === video.id
                        ? "rgba(16, 185, 129, 0.05)"
                        : "transparent",
                    borderLeft:
                      currentVideo.id === video.id
                        ? "3px solid var(--success)"
                        : "3px solid transparent",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    if (currentVideo.id !== video.id)
                      e.currentTarget.style.background = "#f8fafc";
                  }}
                  onMouseLeave={(e) => {
                    if (currentVideo.id !== video.id)
                      e.currentTarget.style.background = "transparent";
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "1rem",
                    }}
                  >
                    <div
                      style={{
                        width: "28px",
                        height: "28px",
                        borderRadius: "50%",
                        background:
                          currentVideo.id === video.id
                            ? "var(--success)"
                            : "var(--bg-primary)",
                        color:
                          currentVideo.id === video.id
                            ? "white"
                            : "var(--text-muted)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "0.75rem",
                        fontWeight: "700",
                        border:
                          currentVideo.id === video.id
                            ? "none"
                            : "1px solid var(--border-light)",
                      }}
                    >
                      {video.order}
                    </div>
                    <div>
                      <h4
                        style={{
                          fontSize: "0.875rem",
                          color:
                            currentVideo.id === video.id
                              ? "var(--text-main)"
                              : "var(--text-muted)",
                          fontWeight:
                            currentVideo.id === video.id ? "600" : "400",
                        }}
                      >
                        {video.title}
                      </h4>
                      <p
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                          marginTop: "0.25rem",
                        }}
                      >
                        {video.duration} mins
                      </p>
                    </div>
                  </div>

                  {currentVideo.id === video.id ? (
                    <PlayCircle size={16} color="var(--success)" />
                  ) : (
                    <PlayCircle size={16} color="var(--border-light)" />
                  )}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WatchLesson;
