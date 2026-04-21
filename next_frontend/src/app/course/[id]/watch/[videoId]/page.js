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
  BookOpen,
  HelpCircle,
  MessageCircle,
} from "lucide-react";
import PrivateRoute from "@/components/PrivateRoute";
import CourseDiscussion from "@/components/CourseDiscussion";
import QuizComponent from "@/components/QuizComponent";
import NotesComponent from "@/components/NotesComponent";


export default function WatchLesson() {
  const params = useParams();
  const courseId = params.id;
  const videoId = params.videoId;
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
  const [actualDuration, setActualDuration] = useState(0);
  const [activeTab, setActiveTab] = useState("discussion"); // 'discussion', 'quiz', 'notes'

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

        const validVideos = courseVideos.filter(v => v.video_url !== null);

        console.log("ALL VIDEOS:", courseVideos);
        console.log("VALID VIDEOS:", validVideos);

        setVideos(validVideos);

        const activeVideo = validVideos.find(
          (v) => v.id === parseInt(videoId),
        );

        setCurrentVideo(activeVideo || validVideos[0]);

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

  const handleVideoMetadataLoaded = () => {
    if (videoRef.current) {
      const duration = videoRef.current.duration;
      if (!isNaN(duration) && duration !== Infinity) {
        setActualDuration(duration);
      } else if (currentVideo?.duration) {
        // Fallback to stored duration in seconds
        setActualDuration(currentVideo.duration * 60);
      }
    }
  };

  const calculateTotalProgress = () => {
    if (!courseProgress) return 0;
    return Math.round(courseProgress.progress_percentage || 0);
  };

  const apiHost = process.env.NEXT_PUBLIC_API_BASE_URL
    ? new URL(process.env.NEXT_PUBLIC_API_BASE_URL).origin
    : "http://localhost:8000";

  const getVideoSrc = (src) => {
    if (!src) return null;

    const parts = src.split("/media/");
    if (parts.length < 2) return src;

    return `${apiHost}/videos/stream/${parts[1]}`;
  };

  const formatVideoDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}:${String(secs).padStart(2, "0")}`;
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
                {currentVideo && currentVideo.video_url ? (
                  <video
                    ref={videoRef}
                    className="lesson-video"
                    key={currentVideo.id}
                    src={getVideoSrc(currentVideo.video_url)}
                    controls
                    autoPlay
                    preload="metadata"
                    onLoadedMetadata={handleVideoMetadataLoaded}
                    onEnded={handleVideoComplete}
                    crossOrigin="anonymous"
                    style={{ width: "100%", height: "100%" }}
                  >
                    {currentVideo.subtitle_url && (
                      <track
                        kind="subtitles"
                        src={currentVideo.subtitle_url}
                        srcLang={currentVideo.subtitle_language || "en"}
                        label={currentVideo.subtitle_label || "English"}
                        default
                      />
                    )}
                    Your browser does not support the video tag.
                  </video>
                ) : (
                  <div style={{ color: "white", textAlign: "center" }}>
                    ⏳ Video is processing...
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
                      marginBottom: "1.5rem",
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
                      <Clock size={16} /> {actualDuration > 0 ? formatVideoDuration(actualDuration) : `${currentVideo.duration}:00`}
                    </div>
                  </div>

                  {/* Tab Navigation */}
                  <div
                    style={{
                      display: "flex",
                      gap: "0.5rem",
                      borderBottom: "2px solid var(--border-light)",
                      marginBottom: "1.5rem",
                    }}
                  >
                    <button
                      onClick={() => setActiveTab("notes")}
                      style={{
                        padding: "0.75rem 1.5rem",
                        background: "none",
                        border: "none",
                        fontSize: "0.95rem",
                        fontWeight: activeTab === "notes" ? "700" : "500",
                        color: activeTab === "notes" ? "var(--accent-primary)" : "var(--text-muted)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        transition: "all 0.2s",
                        borderBottom: activeTab === "notes" ? "3px solid var(--accent-primary)" : "none",
                        marginBottom: "-2px",
                      }}
                      onMouseEnter={(e) => {
                        if (activeTab !== "notes") {
                          e.currentTarget.style.color = "var(--text-main)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeTab !== "notes") {
                          e.currentTarget.style.color = "var(--text-muted)";
                        }
                      }}
                    >
                      <BookOpen size={18} /> Notes
                    </button>

                    <button
                      onClick={() => setActiveTab("quiz")}
                      style={{
                        padding: "0.75rem 1.5rem",
                        background: "none",
                        border: "none",
                        fontSize: "0.95rem",
                        fontWeight: activeTab === "quiz" ? "700" : "500",
                        color: activeTab === "quiz" ? "var(--accent-primary)" : "var(--text-muted)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        transition: "all 0.2s",
                        borderBottom: activeTab === "quiz" ? "3px solid var(--accent-primary)" : "none",
                        marginBottom: "-2px",
                      }}
                      onMouseEnter={(e) => {
                        if (activeTab !== "quiz") {
                          e.currentTarget.style.color = "var(--text-main)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeTab !== "quiz") {
                          e.currentTarget.style.color = "var(--text-muted)";
                        }
                      }}
                    >
                      <HelpCircle size={18} /> Quiz
                    </button>

                    <button
                      onClick={() => setActiveTab("discussion")}
                      style={{
                        padding: "0.75rem 1.5rem",
                        background: "none",
                        border: "none",
                        fontSize: "0.95rem",
                        fontWeight: activeTab === "discussion" ? "700" : "500",
                        color: activeTab === "discussion" ? "var(--accent-primary)" : "var(--text-muted)",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        transition: "all 0.2s",
                        borderBottom: activeTab === "discussion" ? "3px solid var(--accent-primary)" : "none",
                        marginBottom: "-2px",
                      }}
                      onMouseEnter={(e) => {
                        if (activeTab !== "discussion") {
                          e.currentTarget.style.color = "var(--text-main)";
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (activeTab !== "discussion") {
                          e.currentTarget.style.color = "var(--text-muted)";
                        }
                      }}
                    >
                      <MessageCircle size={18} /> Discussion
                    </button>
                  </div>

                  {/* Tab Content */}
                  <div style={{ minHeight: "400px" }}>
                    {activeTab === "notes" && <NotesComponent videoId={currentVideo.id} />}
                    {activeTab === "quiz" && <QuizComponent videoId={currentVideo.id} />}
                    {activeTab === "discussion" && <CourseDiscussion courseId={courseId} />}
                  </div>
                </div>
              )}

              {!currentVideo && (
                <div style={{ marginTop: "2rem", textAlign: "center", color: "var(--text-muted)" }}>
                  <p>No video available</p>
                </div>
              )}
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
        <style jsx global>{`
          video.lesson-video::cue {
            font-size: 0.95rem;
            line-height: 1.25;
            background: rgba(0, 0, 0, 0.72);
            color: #ffffff;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);
          }
        `}</style>
      </div>
    </PrivateRoute>
  );
}
