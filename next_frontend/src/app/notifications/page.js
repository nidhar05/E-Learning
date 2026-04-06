"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Bell, BookOpen, CheckCheck, Clock, RefreshCw } from "lucide-react";

import api from "@/api/client";
import PrivateRoute from "@/components/PrivateRoute";
import { useAuth } from "@/context/AuthContext";

const FILTER_OPTIONS = [
  { label: "All", value: "all" },
  { label: "Unread", value: "unread" },
  { label: "Read", value: "read" },
];

const TYPE_LABELS = {
  comment: "Course comment",
  comment_reply: "Reply",
  enrollment: "Enrollment",
  new_lesson: "New lesson",
};

export default function NotificationsPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchNotifications = async () => {
      if (!user) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const response = await api.get(`notifications/?status=${filter}`);
        setNotifications(response.data);
        setError("");
      } catch (fetchError) {
        console.error("Failed to fetch notifications", fetchError);
        setError("Couldn't load notifications right now. Please try again.");
      }
      setLoading(false);
    };

    fetchNotifications();
  }, [filter, user]);

  const unreadCount = notifications.filter((notification) => !notification.is_read).length;

  const refreshNotifications = async (nextFilter = filter) => {
    try {
      const response = await api.get(`notifications/?status=${nextFilter}`);
      setNotifications(response.data);
      setError("");
    } catch (fetchError) {
      console.error("Failed to fetch notifications", fetchError);
      setError("Couldn't load notifications right now. Please try again.");
    }
  };

  const handleMarkAsRead = async (notificationId, event) => {
    event.stopPropagation();

    try {
      await api.put(`notifications/read/${notificationId}/`);

      if (filter === "unread") {
        setNotifications((prev) => prev.filter((item) => item.id !== notificationId));
      } else {
        setNotifications((prev) =>
          prev.map((item) =>
            item.id === notificationId ? { ...item, is_read: true } : item,
          ),
        );
      }
    } catch (error) {
      console.error("Failed to mark notification as read", error);
    }
  };

  const handleMarkAllRead = async () => {
    setActionLoading(true);

    try {
      await api.put("notifications/read-all/");

      if (filter === "unread") {
        setNotifications([]);
      } else {
        setNotifications((prev) =>
          prev.map((item) => ({
            ...item,
            is_read: true,
          })),
        );
      }
    } catch (error) {
      console.error("Failed to mark all notifications as read", error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenNotification = async (notification) => {
    try {
      if (!notification.is_read) {
        await api.put(`notifications/read/${notification.id}/`);
      }
    } catch (error) {
      console.error("Failed to update notification before navigation", error);
    } finally {
      if (notification.target_url) {
        router.push(notification.target_url);
      }
    }
  };

  return (
    <PrivateRoute>
      <div
        className="animate-fade-in"
        style={{ padding: "2rem", maxWidth: "1100px", margin: "0 auto" }}
      >
        <div
          style={{
            marginBottom: "2rem",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            gap: "1.5rem",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              className="glass-panel"
              style={{
                width: "64px",
                height: "64px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Bell size={28} color="var(--accent-primary)" />
            </div>
            <div>
              <h1 style={{ fontSize: "2.4rem", marginBottom: "0.4rem" }}>
                Notifications
              </h1>
              <p style={{ color: "var(--text-muted)", fontSize: "1rem" }}>
                Track course activity, replies, enrollments, and new lessons in one place.
              </p>
            </div>
          </div>

          <div
            className="glass-panel"
            style={{
              padding: "1rem 1.25rem",
              minWidth: "260px",
              display: "flex",
              flexDirection: "column",
              gap: "0.6rem",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                Current filter
              </span>
              <button
                onClick={() => refreshNotifications()}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent-primary)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  fontWeight: "600",
                }}
              >
                <RefreshCw size={14} />
                Refresh
              </button>
            </div>
            <strong style={{ fontSize: "1.1rem" }}>
              {FILTER_OPTIONS.find((option) => option.value === filter)?.label}
            </strong>
            <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
              {unreadCount} unread in this view
            </div>
          </div>
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "1rem",
            marginBottom: "1.5rem",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            {FILTER_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setFilter(option.value)}
                style={{
                  border: "1px solid var(--border-light)",
                  background:
                    filter === option.value
                      ? "var(--accent-primary)"
                      : "rgba(255,255,255,0.7)",
                  color: filter === option.value ? "white" : "var(--text-main)",
                  borderRadius: "999px",
                  padding: "0.6rem 1rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                {option.label}
              </button>
            ))}
          </div>

          <button
            onClick={handleMarkAllRead}
            disabled={actionLoading || notifications.every((item) => item.is_read)}
            className="btn-secondary"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              opacity:
                actionLoading || notifications.every((item) => item.is_read) ? 0.6 : 1,
            }}
          >
            <CheckCheck size={16} />
            {actionLoading ? "Updating..." : "Mark All Read"}
          </button>
        </div>

        {loading ? (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              padding: "4rem",
            }}
          >
            <div
              style={{
                width: "42px",
                height: "42px",
                border: "4px solid rgba(249, 115, 22, 0.15)",
                borderTopColor: "var(--accent-primary)",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
              }}
            />
          </div>
        ) : error ? (
          <div
            className="glass-panel"
            style={{ padding: "3rem 2rem", textAlign: "center" }}
          >
            <Bell
              size={44}
              color="var(--text-muted)"
              style={{ margin: "0 auto 1rem", opacity: 0.45 }}
            />
            <h3 style={{ marginBottom: "0.75rem" }}>Notifications unavailable</h3>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.25rem" }}>
              {error}
            </p>
            <button onClick={() => refreshNotifications()} className="btn-primary">
              Try Again
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div
            className="glass-panel"
            style={{ padding: "4rem 2rem", textAlign: "center" }}
          >
            <Bell
              size={48}
              color="var(--text-muted)"
              style={{ margin: "0 auto 1.25rem", opacity: 0.5 }}
            />
            <h3 style={{ marginBottom: "0.6rem" }}>No notifications here</h3>
            <p style={{ color: "var(--text-muted)", marginBottom: "1.5rem" }}>
              {filter === "all"
                ? "New activity will show up here as your courses and discussions evolve."
                : `There are no ${filter} notifications right now.`}
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="btn-primary"
            >
              Back to Dashboard
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className="glass-panel"
                onClick={() => handleOpenNotification(notification)}
                style={{
                  padding: "1.25rem 1.5rem",
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "1rem",
                  alignItems: "flex-start",
                  cursor: notification.target_url ? "pointer" : "default",
                  borderLeft: notification.is_read
                    ? "4px solid transparent"
                    : "4px solid var(--accent-primary)",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: "flex",
                      gap: "0.6rem",
                      alignItems: "center",
                      marginBottom: "0.6rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <span
                      style={{
                        background: notification.is_read
                          ? "rgba(148, 163, 184, 0.12)"
                          : "rgba(249, 115, 22, 0.12)",
                        color: notification.is_read
                          ? "var(--text-muted)"
                          : "var(--accent-primary)",
                        borderRadius: "999px",
                        padding: "0.25rem 0.65rem",
                        fontSize: "0.7rem",
                        fontWeight: "700",
                        textTransform: "uppercase",
                        letterSpacing: "0.05em",
                      }}
                    >
                      {TYPE_LABELS[notification.notification_type] || "Notification"}
                    </span>
                    {!notification.is_read && (
                      <span
                        style={{
                          color: "var(--accent-primary)",
                          fontSize: "0.75rem",
                          fontWeight: "700",
                        }}
                      >
                        Unread
                      </span>
                    )}
                  </div>

                  <p
                    style={{
                      margin: "0 0 0.5rem 0",
                      fontSize: "1rem",
                      lineHeight: "1.5",
                      color: "var(--text-main)",
                    }}
                  >
                    {notification.message}
                  </p>

                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                      color: "var(--text-muted)",
                      fontSize: "0.8rem",
                    }}
                  >
                    <Clock size={14} />
                    <span>{new Date(notification.created_at).toLocaleString()}</span>
                    {notification.target_url && (
                      <>
                        <span>•</span>
                        <span style={{ color: "var(--accent-primary)", fontWeight: "600" }}>
                          Open destination
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.65rem",
                    alignItems: "flex-end",
                    minWidth: "140px",
                  }}
                >
                  {notification.target_url ? (
                    <button
                      onClick={(event) => {
                        event.stopPropagation();
                        handleOpenNotification(notification);
                      }}
                      className="btn-secondary"
                      style={{ width: "100%" }}
                    >
                      Open
                    </button>
                  ) : (
                    <button
                      onClick={() => router.push("/dashboard")}
                      className="btn-secondary"
                      style={{ width: "100%" }}
                    >
                      <span style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem" }}>
                        <BookOpen size={14} />
                        Dashboard
                      </span>
                    </button>
                  )}

                  {!notification.is_read && (
                    <button
                      onClick={(event) => handleMarkAsRead(notification.id, event)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--accent-primary)",
                        cursor: "pointer",
                        fontWeight: "600",
                      }}
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PrivateRoute>
  );
}
