import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuth } from "../context/AuthContext";
import {
  ArrowLeft,
  PlayCircle,
  BookOpen,
  CheckCircle,
  Video,
} from "lucide-react";

const CourseDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [enrollLoading, setEnrollLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [courseRes, enrollmentsRes, videosRes] = await Promise.all([
          api.get(`courses/${id}/`),
          user?.role === "student"
            ? api.get("enrollments/")
            : Promise.resolve({ data: [] }),
          api.get("videos/"), // Since the backend doesn't filter by default, we fetch and filter locally for now
        ]);

        setCourse(courseRes.data);

        if (user?.role === "student") {
          const enrolled = enrollmentsRes.data.some(
            (e) => e.course === parseInt(id),
          );
          setIsEnrolled(enrolled);
        }

        const courseVideos = videosRes.data.filter(
          (v) => v.course === parseInt(id),
        );
        setVideos(courseVideos.sort((a, b) => a.order - b.order));
      } catch (err) {
        console.error("Failed to load course details", err);
        setError("Could not load course. It may have been deleted.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, user]);

  const handleEnroll = async () => {
    setEnrollLoading(true);
    try {
      await api.post(`enrollments/enroll/${id}/`);
      setIsEnrolled(true);
    } catch (err) {
      console.error(err);
      setError("Failed to enroll. Please try again later.");
    } finally {
      setEnrollLoading(false);
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

  if (error || !course) {
    return (
      <div
        style={{ padding: "4rem", textAlign: "center", color: "var(--error)" }}
      >
        <h2>{error || "Course not found"}</h2>
        <button
          onClick={() => navigate("/dashboard")}
          className="btn-secondary"
          style={{ marginTop: "1rem" }}
        >
          Go Back
        </button>
      </div>
    );
  }

  const isInstructorOfCourse =
    user?.role === "instructor" && course.instructor === user?.id; // Assuming we have instructor ID, backend Serializer is read-only for instructor, but let's assume UI just shows "Edit" if instructor.

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}
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
        <ArrowLeft size={16} /> Dashboard
      </button>

      <div
        className="glass-panel"
        style={{
          padding: "3rem",
          display: "flex",
          flexDirection: "column",
          gap: "2rem",
        }}
      >
        {/* Header Section */}
        <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
          <div
            style={{
              flex: "1 1 300px",
              height: "250px",
              borderRadius: "12px",
              overflow: "hidden",
              background: "linear-gradient(135deg, #f8fafc, #f1f5f9)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {course.thumbnail ? (
              <img
                src={course.thumbnail}
                alt={course.title}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            ) : (
              <BookOpen size={64} color="rgba(15, 23, 42, 0.1)" />
            )}
          </div>
          <div
            style={{
              flex: "2 1 400px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <h1
              style={{
                fontSize: "2.5rem",
                marginBottom: "1rem",
                color: "var(--text-main)",
              }}
            >
              {course.title}
            </h1>
            <p
              style={{
                color: "var(--text-muted)",
                fontSize: "1.1rem",
                lineHeight: "1.6",
                marginBottom: "2rem",
              }}
            >
              {course.description}
            </p>

            {user?.role === "student" && !isEnrolled && (
              <button
                onClick={handleEnroll}
                disabled={enrollLoading}
                className="btn-primary"
                style={{
                  alignSelf: "flex-start",
                  padding: "0.75rem 2rem",
                  fontSize: "1.1rem",
                }}
              >
                {enrollLoading ? "Enrolling..." : "Enroll Now"}
              </button>
            )}
            {user?.role === "student" && isEnrolled && (
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  color: "var(--success)",
                  fontWeight: "600",
                }}
              >
                <CheckCircle size={20} /> You are enrolled in this course
              </div>
            )}
            {user?.role === "instructor" && (
              <div style={{ display: "flex", gap: "1rem" }}>
                <button
                  onClick={() => navigate(`/course/${id}/edit`)}
                  className="btn-secondary"
                >
                  Edit Course
                </button>
                <button
                  onClick={() => navigate(`/course/${id}/manage`)}
                  className="btn-primary"
                >
                  Manage Curriculum
                </button>
              </div>
            )}
            {user?.role === "instructor" && (
              <div style={{ marginTop: "1rem" }}>
                <button
                  onClick={async () => {
                    if (
                      window.confirm(
                        "Are you sure you want to delete this course? This action cannot be undone.",
                      )
                    ) {
                      try {
                        await api.delete(`courses/${id}/`);
                        navigate("/dashboard");
                      } catch (err) {
                        setError("Failed to delete course.");
                      }
                    }
                  }}
                  style={{
                    background: "transparent",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    color: "var(--error)",
                    padding: "0.5rem 1rem",
                    borderRadius: "8px",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    fontSize: "0.875rem",
                    fontWeight: "600",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
                    e.currentTarget.style.borderColor =
                      "rgba(239, 68, 68, 0.5)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                    e.currentTarget.style.borderColor =
                      "rgba(239, 68, 68, 0.3)";
                  }}
                >
                  Delete Course
                </button>
              </div>
            )}
          </div>
        </div>

        <hr
          style={{
            border: "none",
            borderTop: "1px solid var(--border-light)",
            margin: "1rem 0",
          }}
        />

        {/* Course Curriculum */}
        <div>
          <h2
            style={{
              fontSize: "1.5rem",
              marginBottom: "1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <Video size={24} color="var(--accent-primary)" /> Course Curriculum
          </h2>

          {videos.length === 0 ? (
            <p
              style={{
                color: "var(--text-muted)",
                fontStyle: "italic",
                background: "var(--bg-primary)",
                padding: "1.5rem",
                borderRadius: "8px",
                border: "1px dashed var(--border-light)",
              }}
            >
              {user?.role === "instructor"
                ? "You haven't added any videos yet. Click 'Manage Curriculum' to upload lessons."
                : "The instructor hasn't uploaded any videos yet. Check back soon!"}
            </p>
          ) : (
            <div
              style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
            >
              {videos.map((video, index) => (
                <div
                  key={video.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "1rem 1.5rem",
                    background: "#f8fafc",
                    border: "1px solid var(--border-light)",
                    borderRadius: "8px",
                    transition: "all 0.2s",
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
                        width: "32px",
                        height: "32px",
                        borderRadius: "50%",
                        background: "rgba(249, 115, 22, 0.1)",
                        color: "var(--accent-primary)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontWeight: "700",
                        fontSize: "0.875rem",
                      }}
                    >
                      {video.order || index + 1}
                    </div>
                    <span
                      style={{ fontWeight: "500", color: "var(--text-main)" }}
                    >
                      {video.title}
                    </span>{" "}
                    {/* Assuming video has a title, the model might not though... let's check */}
                  </div>
                  {isEnrolled || user?.role === "instructor" ? (
                    <button
                      onClick={() =>
                        navigate(`/course/${id}/watch/${video.id}`)
                      }
                      className="btn-secondary"
                      style={{
                        padding: "0.5rem 1rem",
                        fontSize: "0.875rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                      }}
                    >
                      <PlayCircle size={16} /> Watch
                    </button>
                  ) : (
                    <span
                      style={{
                        color: "var(--text-muted)",
                        fontSize: "0.875rem",
                      }}
                    >
                      Enroll to view
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseDetail;
