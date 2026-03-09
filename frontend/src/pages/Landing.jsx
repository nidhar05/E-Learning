import React from "react";
import { Link, Navigate } from "react-router-dom";
import { BookOpen, Users, Video, Award, ArrowRight } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const Landing = () => {
  const { user, loading } = useAuth();

  // If already logged in, we might want to let them see the landing page,
  // or redirect them. Let's show the landing page but change the CTA.

  if (loading) {
    return <div style={{ minHeight: "100vh" }}></div>;
  }

  return (
    <div className="animate-fade-in" style={{ paddingBottom: "4rem" }}>
      {/* Hero Section */}
      <section
        style={{
          padding: "6rem 2rem",
          textAlign: "center",
          background:
            "linear-gradient(135deg, rgba(249, 115, 22, 0.05) 0%, rgba(16, 185, 129, 0.05) 100%)",
          borderBottom: "1px solid var(--border-light)",
        }}
      >
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.5rem",
              background: "white",
              padding: "0.5rem 1rem",
              borderRadius: "999px",
              border: "1px solid var(--border-light)",
              boxShadow: "var(--glass-shadow)",
              marginBottom: "2rem",
              fontSize: "0.875rem",
              fontWeight: "600",
              color: "var(--accent-primary)",
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                background: "var(--success)",
                borderRadius: "50%",
                display: "inline-block",
              }}
            ></span>
            Now Available in Beta
          </div>

          <h1
            style={{
              fontSize: "clamp(3rem, 5vw, 4.5rem)",
              lineHeight: "1.1",
              marginBottom: "1.5rem",
              color: "var(--text-main)",
            }}
          >
            Master New Skills with <br />
            <span
              style={{
                background:
                  "linear-gradient(to right, var(--accent-primary), var(--success))",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                display: "inline-block",
              }}
            >
              CollabStudy
            </span>
          </h1>

          <p
            style={{
              fontSize: "1.25rem",
              color: "var(--text-muted)",
              marginBottom: "2.5rem",
              lineHeight: "1.6",
              maxWidth: "600px",
              margin: "0 auto 2.5rem",
            }}
          >
            The premier platform for instructors to build engaging courses and
            students to accelerate their learning journey with interactive video
            lessons.
          </p>

          <div
            style={{
              display: "flex",
              gap: "1rem",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            {user ? (
              <Link
                to="/dashboard"
                className="btn-primary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  padding: "1rem 2rem",
                  fontSize: "1.125rem",
                }}
              >
                Go to Dashboard <ArrowRight size={20} />
              </Link>
            ) : (
              <>
                <Link
                  to="/signup"
                  className="btn-primary"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    padding: "1rem 2rem",
                    fontSize: "1.125rem",
                  }}
                >
                  Start Learning for Free
                </Link>
                <Link
                  to="/login"
                  className="btn-secondary"
                  style={{ padding: "1rem 2rem", fontSize: "1.125rem" }}
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section
        style={{ padding: "5rem 2rem", maxWidth: "1200px", margin: "0 auto" }}
      >
        <div style={{ textAlign: "center", marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>
            Everything You Need to Succeed
          </h2>
          <p
            style={{
              color: "var(--text-muted)",
              fontSize: "1.125rem",
              maxWidth: "600px",
              margin: "0 auto",
            }}
          >
            Built with modern technology to provide a seamless, distraction-free
            learning environment.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "2rem",
          }}
        >
          {/* Feature 1 */}
          <div
            className="glass-panel"
            style={{
              padding: "2rem",
              transition: "transform 0.3s",
              cursor: "default",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.transform = "translateY(-10px)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.transform = "translateY(0)")
            }
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                background: "rgba(249, 115, 22, 0.1)",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1.5rem",
                color: "var(--accent-primary)",
              }}
            >
              <Video size={28} />
            </div>
            <h3 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>
              High-Quality Video Lessons
            </h3>
            <p style={{ color: "var(--text-muted)", lineHeight: "1.6" }}>
              Stream courses seamlessly with our custom video player designed
              for focus and comprehension.
            </p>
          </div>

          {/* Feature 2 */}
          <div
            className="glass-panel"
            style={{
              padding: "2rem",
              transition: "transform 0.3s",
              cursor: "default",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.transform = "translateY(-10px)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.transform = "translateY(0)")
            }
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                background: "var(--success-light)",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1.5rem",
                color: "var(--success)",
              }}
            >
              <Award size={28} />
            </div>
            <h3 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>
              Progress Tracking
            </h3>
            <p style={{ color: "var(--text-muted)", lineHeight: "1.6" }}>
              Automatically track your completed lessons and visualize your
              journey towards mastering the subject.
            </p>
          </div>

          {/* Feature 3 */}
          <div
            className="glass-panel"
            style={{
              padding: "2rem",
              transition: "transform 0.3s",
              cursor: "default",
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.transform = "translateY(-10px)")
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.transform = "translateY(0)")
            }
          >
            <div
              style={{
                width: "56px",
                height: "56px",
                background: "rgba(59, 130, 246, 0.1)",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "1.5rem",
                color: "#3b82f6",
              }}
            >
              <Users size={28} />
            </div>
            <h3 style={{ fontSize: "1.25rem", marginBottom: "0.75rem" }}>
              Expert Instructors
            </h3>
            <p style={{ color: "var(--text-muted)", lineHeight: "1.6" }}>
              Learn directly from industry professionals who create
              comprehensive curriculums just for you.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section style={{ padding: "4rem 2rem" }}>
        <div
          className="glass-panel"
          style={{
            maxWidth: "1000px",
            margin: "0 auto",
            padding: "4rem 2rem",
            textAlign: "center",
            background: "linear-gradient(135deg, white, #f8fafc)",
            border: "1px solid var(--border-light)",
          }}
        >
          <BookOpen
            size={48}
            color="var(--accent-primary)"
            style={{ margin: "0 auto 1.5rem" }}
          />
          <h2 style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>
            Ready to start your journey?
          </h2>
          <p
            style={{
              color: "var(--text-muted)",
              fontSize: "1.125rem",
              marginBottom: "2rem",
            }}
          >
            Join thousands of learners and instructors on CollabStudy today.
          </p>
          {!user && (
            <Link
              to="/signup"
              className="btn-primary"
              style={{ padding: "1rem 2.5rem", fontSize: "1.125rem" }}
            >
              Create your free account
            </Link>
          )}
        </div>
      </section>
    </div>
  );
};

export default Landing;
