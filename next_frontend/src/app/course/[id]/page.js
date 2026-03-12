"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  PlayCircle,
  BookOpen,
  CheckCircle,
  Video,
  Heart
} from "lucide-react";
import PrivateRoute from "@/components/PrivateRoute";
import CourseDiscussion from "@/components/CourseDiscussion";

export default function CourseDetail() {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [isEnrolled, setIsEnrolled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [enrollLoading, setEnrollLoading] = useState(false);
  const [error, setError] = useState("");
  const [wishlistEntryId, setWishlistEntryId] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [courseRes, enrollmentsRes, videosRes, wishlistRes] = await Promise.all([
          api.get(`courses/${id}/`),
          user?.role === "student"
            ? api.get("enrollments/")
            : Promise.resolve({ data: [] }),
          api.get("videos/"),
          user?.role === "student"
            ? api.get("wishlist/")
            : Promise.resolve({ data: [] }),
        ]);

        setCourse(courseRes.data);

        if (user?.role === "student") {
          const enrolled = enrollmentsRes.data.some(
            (e) => e.course === parseInt(id),
          );
          setIsEnrolled(enrolled);

          // Check if in wishlist
          const wishlistItem = wishlistRes.data.find(w => w.course === parseInt(id));
          if (wishlistItem) {
             setWishlistEntryId(wishlistItem.id);
          }
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

    if (id && user) {
      fetchData();
    }
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

  const handleToggleWishlist = async () => {
    try {
      if (wishlistEntryId) {
        // Remove from wishlist
        await api.delete(`wishlist/${wishlistEntryId}/`);
        setWishlistEntryId(null);
      } else {
        // Add to wishlist
        const response = await api.post("wishlist/", { course: id });
        setWishlistEntryId(response.data.id);
      }
    } catch (err) {
      console.error("Failed to update wishlist", err);
    }
  };

  if (loading) {
    return (
      <PrivateRoute>
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
      </PrivateRoute>
    );
  }

  if (error || !course) {
    return (
      <PrivateRoute>
        <div
          style={{
            padding: "4rem",
            textAlign: "center",
            color: "var(--error)",
          }}
        >
          <h2>{error || "Course not found"}</h2>
          <button
            onClick={() => router.push("/dashboard")}
            className="btn-secondary"
            style={{ marginTop: "1rem" }}
          >
            Go Back
          </button>
        </div>
      </PrivateRoute>
    );
  }

  return (
    <PrivateRoute>
      <div
        className="animate-fade-in"
        style={{ padding: "2rem", maxWidth: "1000px", margin: "0 auto" }}
      >
        <button
          onClick={() => router.push("/dashboard")}
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
                  marginBottom: "0.5rem",
                  color: "var(--text-main)",
                }}
              >
                {course.title}
              </h1>
              <div style={{ fontSize: "1rem", color: "var(--accent-primary)", fontWeight: "600", marginBottom: "1.5rem" }}>
                Created by {course.instructor_name}
              </div>
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
                    marginBottom: "1rem"
                  }}
                >
                  <CheckCircle size={20} /> You are enrolled in this course
                </div>
              )}
              
              {user?.role === "student" && (
                <button
                  onClick={handleToggleWishlist}
                  style={{
                    width: "fit-content",
                    padding: "0.5rem 1rem",
                    marginTop: isEnrolled ? "0" : "1rem",
                    border: "1px solid var(--border-color)",
                    background: wishlistEntryId ? "rgba(220, 38, 38, 0.1)" : "transparent",
                    color: wishlistEntryId ? "rgb(220, 38, 38)" : "var(--text-main)",
                    borderRadius: "0.5rem",
                    fontWeight: "600",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.5rem",
                    transition: "all 0.2s"
                  }}
                >
                  <Heart size={20} fill={wishlistEntryId ? "currentColor" : "none"} />
                  {wishlistEntryId ? "Remove from Wishlist" : "Add to Wishlist"}
                </button>
              )}
              {user?.role === "instructor" && (
                <div style={{ display: "flex", gap: "1rem" }}>
                  <button
                    onClick={() => router.push(`/course/${id}/edit`)}
                    className="btn-secondary"
                  >
                    Edit Course
                  </button>
                  <button
                    onClick={() => router.push(`/course/${id}/manage`)}
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
                          router.push("/dashboard");
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
                      e.currentTarget.style.background =
                        "rgba(239, 68, 68, 0.1)";
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
              <Video size={24} color="var(--accent-primary)" /> Course
              Curriculum
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
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
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
                      </span>
                    </div>
                    {isEnrolled || user?.role === "instructor" ? (
                      <button
                        onClick={() =>
                          router.push(`/course/${id}/watch/${video.id}`)
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
            
            {/* Discussion Section */}
            <div style={{ marginTop: "4rem" }}>
              <CourseDiscussion courseId={id} />
            </div>
            
          </div>
        </div>
      </div>
    </PrivateRoute>
  );
}
