import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { BookOpen, LogOut, LayoutDashboard } from "lucide-react";

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(255, 255, 255, 0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--border-light)",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
        padding: "1rem 2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <Link
        to={user ? "/dashboard" : "/"}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
          fontSize: "1.25rem",
          fontWeight: "700",
          color: "var(--text-main)",
        }}
      >
        <BookOpen color="var(--accent-primary)" size={28} />
        CollabStudy
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "1.5rem" }}>
        {user ? (
          <>
            <span style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
              Welcome,{" "}
              <strong style={{ color: "var(--text-main)" }}>
                {user.username}
              </strong>
              <span
                style={{
                  marginLeft: "0.5rem",
                  padding: "0.25rem 0.6rem",
                  background:
                    user.role === "instructor"
                      ? "rgba(249, 115, 22, 0.1)"
                      : "rgba(16, 185, 129, 0.1)",
                  color:
                    user.role === "instructor"
                      ? "var(--accent-primary)"
                      : "var(--success)",
                  border:
                    user.role === "instructor"
                      ? "1px solid rgba(249, 115, 22, 0.2)"
                      : "1px solid rgba(16, 185, 129, 0.2)",
                  borderRadius: "999px",
                  fontSize: "0.75rem",
                  fontWeight: "600",
                }}
              >
                {user.role}
              </span>
            </span>
            <Link
              to="/dashboard"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                color: "var(--text-main)",
              }}
            >
              <LayoutDashboard size={18} />
              Dashboard
            </Link>
            <button
              onClick={handleLogout}
              style={{
                background: "transparent",
                border: "1px solid rgba(239, 68, 68, 0.3)",
                color: "var(--error)",
                padding: "0.5rem 1rem",
                borderRadius: "8px",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                cursor: "pointer",
                transition: "all 0.2s",
                fontSize: "0.875rem",
                fontWeight: "600",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(239, 68, 68, 0.1)";
                e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.5)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.borderColor = "rgba(239, 68, 68, 0.3)";
              }}
            >
              <LogOut size={16} />
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" style={{ color: "var(--text-main)" }}>
              Sign In
            </Link>
            <Link
              to="/signup"
              className="btn-primary"
              style={{ padding: "0.5rem 1rem" }}
            >
              Get Started
            </Link>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
