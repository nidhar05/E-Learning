"use client";

import React, { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import {
  ArrowLeft,
  PlayCircle,
  CheckCircle,
  Clock,
  Menu,
  X,
} from "lucide-react";
import PrivateRoute from "@/components/PrivateRoute";
import CourseDiscussion from "@/components/CourseDiscussion";

export default function WatchLesson() {
  const { id: courseId, videoId } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const videoRef = useRef(null);

  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [courseProgress, setCourseProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const fetchLessonData = async () => {
      try {
        const [courseRes, videosRes] = await Promise.all([
          api.get(`courses/${courseId}/`),
          api.get("videos/"),
        ]);
        
        // Progress is handled below independently so the page doesn't crash if it fails
        
        setCourse(courseRes.data);

        const courseVideos = videosRes.data
          .filter((v) => v.course === parseInt(courseId))
          .sort((a, b) => a.order - b.order);

        setVideos(courseVideos);

        const activeVideo = courseVideos.find(
          (v) => v.id === parseInt(videoId),
        );
        setCurrentVideo(activeVideo || courseVideos[0]);

        if (user?.role === "student") {
          try {
            const progressRes = await api.get(`progress/${courseId}/`);
            setCourseProgress(progressRes.data);
          } catch (e) {
            console.error("Failed to load progress", e);
          }
        }
      } catch (err) {
        console.error("Failed to load lesson data", err);
        setError(
          "Could not load lesson content. Make sure you are enrolled.",
        );
      } finally {
        setLoading(false);
      }
    };

    if (courseId && user) {
      fetchLessonData();
    }
  }, [courseId, videoId, user]);

  const handleVideoComplete = async () => {
    if (user?.role === "student" && currentVideo) {
      try {
        await api.post(`progress/complete/${currentVideo.id}/`);
        // Refresh progress
        const progressRes = await api.get(`progress/${courseId}/`);
        setCourseProgress(progressRes.data);
      } catch (err) {
        console.error("Failed to mark progress", err);
      }
    }
  };

  const calculateTotalProgress = () => {
    if (!courseProgress) return 0;
    return Math.round(courseProgress.progress_percentage || 0);
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
          style={{ padding: "4rem", textAlign: "center", color: "var(--error)" }}
        >
          <h2>{error || "Content not found"}</h2>
          <button
            onClick={() => router.push(`/course/${courseId}`)}
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
      <div style={{ display: "flex", minHeight: "calc(100vh - 56px)" }}>
        {/* Main Content Area */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            position: "relative",
          }}
        >
          {/* Top Bar inside main container (mobile friendly) */}
          <div
            style={{
              padding: "1rem 2rem",
              background: "white",
              borderBottom: "1px solid var(--border-light)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <button
              onClick={() => router.push(`/course/${courseId}`)}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-muted)",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                fontSize: "0.875rem",
                fontWeight: "600",
              }}
            >
              <ArrowLeft size={16} /> Course Overview
            </button>
            <div style={{ fontWeight: "600" }}>{course.title}</div>
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                style={{
                  background: "var(--accent-primary)",
                  border: "none",
                  padding: "0.5rem 0.85rem",
                  borderRadius: "8px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.4rem",
                  color: "white",
                  fontSize: "0.8rem",
                  fontWeight: "600",
                  transition: "all 0.2s",
                }}
              >
                <Menu size={16} /> Course Content
              </button>
            )}
          </div>

          <div
            style={{
              flex: 1,
              padding: "2rem",
              background: "var(--bg-secondary)", 
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              style={{ maxWidth: "1000px", margin: "0 auto", width: "100%" }}
            >
              <div
                style={{
                  width: "100%",
                  aspectRatio: "16/9",
                  background: "black",
                  borderRadius: "12px",
                  overflow: "hidden",
                  boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
                }}
              >
                {currentVideo ? (
                  <video
                    ref={videoRef}
                    key={currentVideo.id} // Forces React to recreate video tag on source change
                    src={currentVideo.video_file}
                    controls
                    autoPlay
                    onEnded={handleVideoComplete}
                    style={{ width: "100%", height: "100%", outline: "none" }}
                  >
                    Your browser does not support HTML5 video.
                  </video>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      height: "100%",
                      color: "rgba(255,255,255,0.8)",
                    }}
                  >
                    No video selected
                  </div>
                )}
              </div>

              {currentVideo && (
                <div style={{ marginTop: "2rem", color: "var(--text-main)" }}>
                  <h2
                    style={{
                      fontSize: "2rem",
                      marginBottom: "0.5rem",
                      color: "var(--text-main)",
                    }}
                  >
                    {currentVideo.order}. {currentVideo.title}
                  </h2>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "1.5rem",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        color: "var(--text-muted)",
                      }}
                    >
                      <Clock size={16} /> {currentVideo.duration} mins
                    </div>
                  </div>
                </div>
              )}
              
              <div style={{ marginTop: "3rem" }}>
                <CourseDiscussion courseId={courseId} />
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Curriculum (Playlist) */}
        {sidebarOpen && (
          <div
            style={{
              width: "350px",
              background: "white",
              borderLeft: "1px solid var(--border-light)",
              display: "flex",
              flexDirection: "column",
              height: "calc(100vh - 56px)",
              position: "sticky",
              top: "0",
              overflowY: "auto",
            }}
          >
            <div
              style={{
                padding: "1.5rem",
                borderBottom: "1px solid var(--border-light)",
                position: "sticky",
                top: 0,
                background: "white",
                zIndex: 10,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3 style={{ fontSize: "1.25rem", margin: 0 }}>
                  Course Content
                </h3>
                <button
                  onClick={() => setSidebarOpen(false)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    color: "var(--text-muted)",
                    padding: "0.25rem",
                    display: "flex",
                    alignItems: "center",
                    borderRadius: "6px",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "var(--bg-primary)"; e.currentTarget.style.color = "var(--text-main)"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "none"; e.currentTarget.style.color = "var(--text-muted)"; }}
                >
                  <X size={18} />
                </button>
              </div>

              {user?.role === "student" && (
                <div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "0.875rem",
                      marginBottom: "0.5rem",
                      color: "var(--text-muted)",
                    }}
                  >
                    <span>{calculateTotalProgress()}% Complete</span>
                    <span>
                      {courseProgress ? `${courseProgress.completed_videos}/${courseProgress.total_videos} Completed` : "Loading..."}
                    </span>
                  </div>
                  <div
                    style={{
                      height: "6px",
                      background: "var(--bg-primary)",
                      borderRadius: "999px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${calculateTotalProgress()}%`,
                        background: "var(--success)",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div style={{ flex: 1, padding: "1rem" }}>
              {videos.map((video, index) => {
                const isActive = currentVideo?.id === video.id;

                return (
                  <button
                    key={video.id}
                    onClick={() =>
                      router.push(`/course/${courseId}/watch/${video.id}`)
                    }
                    style={{
                      width: "100%",
                      textAlign: "left",
                      background: isActive ? "var(--bg-primary)" : "transparent",
                      border: "none",
                      borderLeft: isActive
                        ? "4px solid var(--accent-primary)"
                        : "4px solid transparent",
                      padding: "1rem",
                      borderRadius: "0 8px 8px 0",
                      marginBottom: "0.5rem",
                      cursor: "pointer",
                      display: "flex",
                      gap: "1rem",
                      transition: "all 0.2s",
                    }}
                    onMouseEnter={(e) => {
                      if (!isActive)
                        e.currentTarget.style.background = "#f8fafc";
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive)
                        e.currentTarget.style.background = "transparent";
                    }}
                  >
                    <div
                      style={{
                        color: isActive
                            ? "var(--accent-primary)"
                            : "var(--text-muted)",
                        marginTop: "0.125rem",
                      }}
                    >
                      <PlayCircle size={20} />
                    </div>
                    <div>
                      <h4
                        style={{
                          fontSize: "0.875rem",
                          color: isActive
                            ? "var(--accent-primary)"
                            : "var(--text-main)",
                          marginBottom: "0.25rem",
                          fontWeight: isActive ? "600" : "500",
                        }}
                      >
                        {video.order || index + 1}. {video.title}
                      </h4>
                      <p
                        style={{
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        {video.duration} mins
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </PrivateRoute>
  );
}
