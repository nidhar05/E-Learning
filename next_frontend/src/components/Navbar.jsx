"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useAuth } from "../context/AuthContext";
import { BookOpen, Bell } from "lucide-react";
import api from "@/api/client";

const Navbar = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        const res = await api.get("notifications/");
        setNotifications(res.data);
      } catch (err) {
        console.warn("Failed to fetch notifications", err.response?.status || err.message);
      }
    };

    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [user]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleMarkAsRead = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.put(`notifications/read/${id}/`);
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (err) {
      console.warn("Failed to mark notification as read");
    }
  };

  const handleMarkAllRead = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
       await Promise.all(notifications.map(n => api.put(`notifications/read/${n.id}/`)));
       setNotifications([]);
       setShowNotifications(false);
    } catch (err) {
       console.warn("Failed to mark all as read");
    }
  };

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(255, 255, 255, 0.92)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--border-light)",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
        padding: "0.6rem 2rem",
        paddingLeft: user ? "calc(60px + 2rem)" : "2rem",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        height: "56px",
        transition: "padding-left 0.25s ease",
      }}
    >
      <Link
        href={user ? "/dashboard" : "/"}
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.6rem",
          fontSize: "1.15rem",
          fontWeight: "700",
          color: "var(--text-main)",
        }}
      >
        <BookOpen color="var(--accent-primary)" size={24} />
        CollabStudy
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        {user ? (
          <>
            {/* User Info */}
            <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Welcome,{" "}
              <strong style={{ color: "var(--text-main)" }}>
                {user.username}
              </strong>
              <span
                style={{
                  marginLeft: "0.5rem",
                  padding: "0.15rem 0.5rem",
                  background:
                    user.role === "instructor"
                      ? "rgba(249, 115, 22, 0.1)"
                      : "rgba(16, 185, 129, 0.08)",
                  color:
                    user.role === "instructor"
                      ? "var(--accent-primary)"
                      : "var(--success)",
                  border:
                    user.role === "instructor"
                      ? "1px solid rgba(249, 115, 22, 0.2)"
                      : "1px solid rgba(16, 185, 129, 0.15)",
                  borderRadius: "999px",
                  fontSize: "0.65rem",
                  fontWeight: "600",
                  textTransform: "capitalize",
                }}
              >
                {user.role}
              </span>
            </span>

            {/* Notifications */}
            <div style={{ position: "relative" }} ref={dropdownRef}>
                <button
                  onClick={() => setShowNotifications(!showNotifications)}
                  title="Notifications"
                  style={{
                    background: showNotifications ? "var(--bg-primary)" : "transparent",
                    border: "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "var(--text-muted)",
                    width: "34px",
                    height: "34px",
                    borderRadius: "8px",
                    transition: "all 0.2s",
                    cursor: "pointer",
                    position: "relative"
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "var(--bg-primary)"; e.currentTarget.style.color = "var(--text-main)"; }}
                  onMouseLeave={e => { if(!showNotifications) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "var(--text-muted)"; }}}
                >
                  <Bell size={18} />
                  {notifications.length > 0 && (
                      <span style={{
                          position: "absolute",
                          top: "2px",
                          right: "2px",
                          background: "var(--error)",
                          color: "white",
                          borderRadius: "50%",
                          width: "16px",
                          height: "16px",
                          fontSize: "10px",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontWeight: "bold",
                          border: "2px solid white"
                      }}>
                          {notifications.length > 9 ? "9+" : notifications.length}
                      </span>
                  )}
                </button>

                {/* Dropdown Menu */}
                {showNotifications && (
                  <div style={{
                      position: "absolute",
                      top: "calc(100% + 8px)",
                      right: 0,
                      width: "360px",
                      background: "white",
                      border: "1px solid var(--border-light)",
                      borderRadius: "12px",
                      boxShadow: "0 10px 40px rgba(0,0,0,0.12)",
                      zIndex: 100,
                      overflow: "hidden",
                      display: "flex",
                      flexDirection: "column",
                      maxHeight: "420px"
                  }}>
                      <div style={{ padding: "1rem 1.25rem", borderBottom: "1px solid var(--border-light)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <h3 style={{ margin: 0, fontSize: "0.95rem", color: "var(--text-main)", fontWeight: "700" }}>Notifications</h3>
                          {notifications.length > 0 && (
                             <button 
                                onClick={handleMarkAllRead}
                                style={{ background: "none", border: "none", color: "var(--accent-primary)", fontSize: "0.75rem", cursor: "pointer", fontWeight: "600" }}
                             >
                                 Mark all read
                             </button>
                          )}
                      </div>
                      
                      <div style={{ flex: 1, overflowY: "auto" }}>
                          {notifications.length === 0 ? (
                              <div style={{ padding: "3rem 2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
                                  <Bell size={32} style={{ opacity: 0.15, marginBottom: "0.75rem" }} />
                                  <p style={{ margin: 0 }}>You&apos;re all caught up!</p>
                              </div>
                          ) : (
                              notifications.map(notif => (
                                  <div key={notif.id} style={{ padding: "0.875rem 1.25rem", borderBottom: "1px solid var(--border-light)", display: "flex", gap: "0.75rem", alignItems: "flex-start", transition: "background 0.15s", cursor: "default" }} onMouseEnter={e => e.currentTarget.style.background = "#f8fafc"} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                      <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--accent-primary)", marginTop: "6px", flexShrink: 0 }} />
                                      <div style={{ flex: 1 }}>
                                          <p style={{ margin: "0 0 0.25rem 0", fontSize: "0.85rem", color: "var(--text-main)", lineHeight: "1.4" }}>
                                              {notif.message}
                                          </p>
                                          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
                                              {new Date(notif.created_at).toLocaleString()}
                                          </div>
                                      </div>
                                      <button 
                                          onClick={(e) => handleMarkAsRead(notif.id, e)}
                                          title="Dismiss"
                                          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: "4px", fontSize: "1rem", lineHeight: 1 }}
                                          onMouseEnter={e => e.currentTarget.style.color = "var(--error)"}
                                          onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
                                      >
                                          &times;
                                      </button>
                                  </div>
                              ))
                          )}
                      </div>
                  </div>
                )}
            </div>
          </>
        ) : (
          <>
            <Link href="/login" style={{ color: "var(--text-main)", fontSize: "0.875rem", fontWeight: "500" }}>
              Sign In
            </Link>
            <Link
              href="/signup"
              className="btn-primary"
              style={{ padding: "0.5rem 1.25rem", fontSize: "0.875rem" }}
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
