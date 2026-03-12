import React, { useState, useEffect } from "react";
import { MessageSquare, Send, Reply, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import api from "@/api/client";
import { useAuth } from "@/context/AuthContext";

const AVATAR_COLORS = [
  "#f97316", "#10b981", "#3b82f6", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f59e0b", "#6366f1",
  "#ef4444", "#06b6d4", "#84cc16", "#e11d48",
];

function getUserColor(name) {
  let hash = 0;
  for (let i = 0; i < (name || "").length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function timeAgo(dateString) {
  const seconds = Math.floor((new Date() - new Date(dateString)) / 1000);
  if (seconds < 60) return "just now";
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 7) return `${d}d ago`;
  if (d < 30) return `${Math.floor(d / 7)}w ago`;
  return new Date(dateString).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function Avatar({ name, size = 32 }) {
  const color = getUserColor(name);
  return (
    <div style={{
      width: size, height: size, borderRadius: "50%",
      background: color + "1a", color: color,
      display: "flex", alignItems: "center", justifyContent: "center",
      fontWeight: "700", fontSize: size * 0.4, flexShrink: 0,
    }}>
      {(name || "?").charAt(0).toUpperCase()}
    </div>
  );
}

export default function CourseDiscussion({ courseId }) {
  const { user } = useAuth();
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");
  const [replyText, setReplyText] = useState("");
  const [replyingTo, setReplyingTo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);
  const [expandedReplies, setExpandedReplies] = useState({});
  const [error, setError] = useState("");
  const [confirmingDelete, setConfirmingDelete] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const fetchComments = async () => {
    try {
      const res = await api.get(`comments/?course=${courseId}`);
      setComments(res.data);
    } catch { /* silent */ } finally { setLoading(false); }
  };

  useEffect(() => { if (courseId) fetchComments(); }, [courseId]);

  const handleSubmit = async (e, parentId = null) => {
    e.preventDefault();
    const text = parentId ? replyText : newComment;
    if (text.trim().length < 3) { setError("Must be at least 3 characters."); return; }
    setError("");
    try {
      await api.post("comments/", { course: courseId, text, parent: parentId });
      if (parentId) {
        setReplyText(""); setReplyingTo(null);
        setExpandedReplies(p => ({ ...p, [parentId]: true }));
      } else { setNewComment(""); }
      fetchComments();
    } catch (err) {
      setError(err.response?.data?.text?.[0] || "Failed to post.");
    }
  };

  const handleDelete = async (id) => {
    setDeleting(id);
    try { await api.delete(`comments/${id}/`); fetchComments(); } catch { /* silent */ }
    finally { setDeleting(null); setConfirmingDelete(null); }
  };

  if (loading) return null;

  return (
    <div>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          width: "100%", display: "flex", alignItems: "center",
          justifyContent: "space-between", background: "none",
          border: "none", cursor: "pointer", padding: "0.75rem 0",
          marginBottom: expanded ? "1rem" : 0,
        }}
      >
        <h2 style={{ fontSize: "1.15rem", display: "flex", alignItems: "center", gap: "0.5rem", color: "var(--text-main)", margin: 0 }}>
          <MessageSquare size={20} color="var(--accent-primary)" />
          Discussion
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontWeight: "400" }}>({comments.length})</span>
        </h2>
        {expanded ? <ChevronUp size={16} color="var(--text-muted)" /> : <ChevronDown size={16} color="var(--text-muted)" />}
      </button>

      {expanded && (
        <>
          {/* Comment Input */}
          {user?.role === "student" && (
            <form onSubmit={(e) => handleSubmit(e, null)} style={{ marginBottom: "1.5rem" }}>
              <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
                <Avatar name={user.username} size={36} />
                <input
                  type="text"
                  value={newComment}
                  onChange={(e) => { setNewComment(e.target.value); setError(""); }}
                  placeholder="Add a comment..."
                  style={{ flex: 1, margin: 0 }}
                />
                <button type="submit" className="btn-primary" disabled={newComment.trim().length < 3} style={{ padding: "0.5rem 1rem" }}>
                  <Send size={15} />
                </button>
              </div>
              {error && <p style={{ color: "var(--error)", fontSize: "0.75rem", marginTop: "0.4rem", marginLeft: "3rem" }}>{error}</p>}
            </form>
          )}

          {/* Comment List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0" }}>
            {comments.length === 0 ? (
              <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem", border: "1px dashed var(--border-light)", borderRadius: "8px" }}>
                No discussions yet. Be the first!
              </div>
            ) : (
              comments.map((comment) => (
                <div key={comment.id} style={{ padding: "1rem 0", borderBottom: "1px solid var(--border-light)" }}>

                  {/* Comment Row */}
                  <div style={{ display: "flex", gap: "0.75rem" }}>
                    <Avatar name={comment.user} size={32} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      {/* Meta line */}
                      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.2rem", flexWrap: "wrap" }}>
                        <span style={{ fontWeight: "600", fontSize: "0.85rem", color: "var(--text-main)" }}>{comment.user}</span>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{timeAgo(comment.created_at)}</span>
                      </div>
                      {/* Text */}
                      <p style={{ margin: "0 0 0.4rem", fontSize: "0.875rem", color: "var(--text-main)", lineHeight: "1.5" }}>{comment.text}</p>
                      {/* Actions */}
                      <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                        {user?.role === "instructor" && replyingTo !== comment.id && (
                          <button onClick={() => setReplyingTo(comment.id)} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "0.8rem", cursor: "pointer", display: "flex", alignItems: "center", gap: "0.3rem", padding: 0, fontWeight: "500" }}
                            onMouseEnter={e => e.currentTarget.style.color = "var(--text-main)"}
                            onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
                          >
                            <Reply size={14} /> Reply
                          </button>
                        )}
                        {user && user.username === comment.user && (
                          confirmingDelete === comment.id ? (
                            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.75rem" }}>
                              <span style={{ color: "var(--error)", fontWeight: "500" }}>Delete?</span>
                              <button
                                onClick={() => handleDelete(comment.id)}
                                disabled={deleting === comment.id}
                                style={{ background: "none", border: "1px solid var(--error)", borderRadius: "4px", cursor: "pointer", color: "var(--error)", padding: "0.15rem 0.4rem", fontSize: "0.7rem", fontWeight: "600" }}
                              >
                                {deleting === comment.id ? "..." : "Yes"}
                              </button>
                              <button
                                onClick={() => setConfirmingDelete(null)}
                                style={{ background: "none", border: "1px solid var(--border-light)", borderRadius: "4px", cursor: "pointer", color: "var(--text-muted)", padding: "0.15rem 0.4rem", fontSize: "0.7rem" }}
                              >
                                No
                              </button>
                            </div>
                          ) : (
                            <button onClick={() => setConfirmingDelete(comment.id)} title="Delete" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0, display: "flex", alignItems: "center", gap: "0.25rem", fontSize: "0.8rem" }}
                              onMouseEnter={e => e.currentTarget.style.color = "var(--error)"}
                              onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
                            >
                              <Trash2 size={13} />
                            </button>
                          )
                        )}
                      </div>

                      {/* Reply Form */}
                      {replyingTo === comment.id && (
                        <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem", alignItems: "center" }}>
                          <Avatar name={user.username} size={24} />
                          <input
                            type="text" value={replyText} autoFocus
                            onChange={(e) => setReplyText(e.target.value)}
                            placeholder="Add a reply..."
                            style={{ flex: 1, margin: 0, padding: "0.4rem 0.75rem", fontSize: "0.8rem" }}
                          />
                          <button type="button" className="btn-secondary" style={{ padding: "0.35rem 0.7rem", fontSize: "0.75rem" }} onClick={() => { setReplyingTo(null); setReplyText(""); }}>Cancel</button>
                          <button type="button" className="btn-primary" style={{ padding: "0.35rem 0.7rem", fontSize: "0.75rem" }} disabled={replyText.trim().length < 3} onClick={(e) => handleSubmit(e, comment.id)}>Reply</button>
                        </div>
                      )}

                      {/* Replies Toggle */}
                      {comment.replies?.length > 0 && (
                        <div style={{ marginTop: "0.5rem" }}>
                          <button
                            onClick={() => setExpandedReplies(p => ({ ...p, [comment.id]: !p[comment.id] }))}
                            style={{
                              background: "none", border: "none", cursor: "pointer",
                              color: "var(--accent-primary)", fontSize: "0.8rem",
                              fontWeight: "600", display: "flex", alignItems: "center",
                              gap: "0.3rem", padding: "0.25rem 0",
                            }}
                          >
                            {expandedReplies[comment.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            {comment.replies.length} {comment.replies.length === 1 ? "reply" : "replies"}
                          </button>

                          {/* Expanded Replies */}
                          {expandedReplies[comment.id] && (
                            <div style={{ marginTop: "0.25rem", display: "flex", flexDirection: "column", gap: "0" }}>
                              {comment.replies.map(reply => (
                                <div key={reply.id} style={{ display: "flex", gap: "0.6rem", padding: "0.6rem 0" }}>
                                  <Avatar name={reply.user} size={24} />
                                  <div style={{ flex: 1, minWidth: 0 }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.15rem", flexWrap: "wrap" }}>
                                      <span style={{ fontWeight: "600", fontSize: "0.8rem", color: "var(--text-main)" }}>{reply.user}</span>
                                      <span style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{timeAgo(reply.created_at)}</span>
                                    </div>
                                    <p style={{ margin: 0, fontSize: "0.825rem", color: "var(--text-main)", lineHeight: "1.45" }}>{reply.text}</p>
                                    {user && user.username === reply.user && (
                                      confirmingDelete === reply.id ? (
                                        <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.7rem", marginTop: "0.25rem" }}>
                                          <span style={{ color: "var(--error)", fontWeight: "500" }}>Delete?</span>
                                          <button
                                            onClick={() => handleDelete(reply.id)}
                                            disabled={deleting === reply.id}
                                            style={{ background: "none", border: "1px solid var(--error)", borderRadius: "4px", cursor: "pointer", color: "var(--error)", padding: "0.1rem 0.35rem", fontSize: "0.65rem", fontWeight: "600" }}
                                          >
                                            {deleting === reply.id ? "..." : "Yes"}
                                          </button>
                                          <button
                                            onClick={() => setConfirmingDelete(null)}
                                            style={{ background: "none", border: "1px solid var(--border-light)", borderRadius: "4px", cursor: "pointer", color: "var(--text-muted)", padding: "0.1rem 0.35rem", fontSize: "0.65rem" }}
                                          >
                                            No
                                          </button>
                                        </div>
                                      ) : (
                                        <button onClick={() => setConfirmingDelete(reply.id)} title="Delete" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", padding: 0, marginTop: "0.25rem", display: "flex", alignItems: "center" }}
                                          onMouseEnter={e => e.currentTarget.style.color = "var(--error)"}
                                          onMouseLeave={e => e.currentTarget.style.color = "var(--text-muted)"}
                                        >
                                          <Trash2 size={12} />
                                        </button>
                                      )
                                    )}
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
