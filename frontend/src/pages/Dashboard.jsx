import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import api from "../api/client";
import { PlusCircle, PlayCircle, Clock } from "lucide-react";

const Dashboard = () => {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const response = await api.get("courses/");
        setCourses(response.data);
      } catch (error) {
        console.error("Failed to fetch courses", error);
      } finally {
        setLoading(false);
      }
    };
    fetchCourses();
  }, []);

  return (
    <div
      className="animate-fade-in"
      style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2.5rem",
        }}
      >
        <div>
          <h1 style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>
            My Learning Space
          </h1>
          <p>Explore your courses and resume where you left off</p>
        </div>

        {user?.role === "instructor" && (
          <Link
            to="/create-course"
            className="btn-primary"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              textDecoration: "none",
            }}
          >
            <PlusCircle size={20} />
            Create Course
          </Link>
        )}
      </div>

      {loading ? (
        <div
          style={{ display: "flex", justifyContent: "center", padding: "4rem" }}
        >
          <div
            style={{
              width: "40px",
              height: "40px",
              border: "3px solid rgba(59, 130, 246, 0.2)",
              borderTopColor: "var(--accent-primary)",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        </div>
      ) : courses.length > 0 ? (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "2rem",
          }}
        >
          {courses.map((course) => (
            <div
              key={course.id}
              className="glass-panel"
              style={{
                overflow: "hidden",
                transition: "transform 0.3s, box-shadow 0.3s",
                cursor: "pointer",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-5px)";
                e.currentTarget.style.boxShadow =
                  "0 20px 25px -5px rgba(249, 115, 22, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "var(--glass-shadow)";
              }}
            >
              <div
                style={{
                  height: "160px",
                  background: "linear-gradient(135deg, #f8fafc, #f1f5f9)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                  borderBottom: "1px solid var(--border-light)",
                }}
              >
                {course.thumbnail ? (
                  <img
                    src={course.thumbnail}
                    alt={course.title}
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "cover",
                    }}
                  />
                ) : (
                  <PlayCircle size={48} color="rgba(15, 23, 42, 0.1)" />
                )}
                <div
                  style={{
                    position: "absolute",
                    top: "1rem",
                    right: "1rem",
                    background: "rgba(255, 255, 255, 0.9)",
                    backdropFilter: "blur(4px)",
                    padding: "0.25rem 0.75rem",
                    borderRadius: "999px",
                    fontSize: "0.75rem",
                    fontWeight: "700",
                    color: "var(--accent-primary)",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
                  }}
                >
                  Course
                </div>
              </div>
              <div style={{ padding: "1.5rem" }}>
                <h3 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>
                  {course.title}
                </h3>
                <p
                  style={{
                    fontSize: "0.875rem",
                    marginBottom: "1.5rem",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {course.description ||
                    "No description provided for this course."}
                </p>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    paddingTop: "1rem",
                    borderTop: "1px solid var(--border-light)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      color: "var(--text-muted)",
                      fontSize: "0.875rem",
                    }}
                  >
                    <Clock size={16} />
                    <span>View details</span>
                  </div>
                  <Link
                    to={`/course/${course.id}`}
                    className="btn-secondary"
                    style={{
                      padding: "0.5rem 1rem",
                      fontSize: "0.875rem",
                      textDecoration: "none",
                    }}
                  >
                    Open
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div
          className="glass-panel"
          style={{ padding: "4rem 2rem", textAlign: "center" }}
        >
          <BookOpen
            size={48}
            color="var(--text-muted)"
            style={{ margin: "0 auto 1.5rem", opacity: 0.5 }}
          />
          <h3>No courses found</h3>
          <p style={{ marginTop: "0.5rem" }}>
            {user?.role === "instructor"
              ? "You haven't created any courses yet. Get started by clicking 'Create Course'."
              : "There are no active courses available right now."}
          </p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
