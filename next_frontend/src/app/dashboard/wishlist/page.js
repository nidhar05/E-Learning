"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { BookOpen, User as UserIcon, Heart, Trash2 } from "lucide-react";
import PrivateRoute from "@/components/PrivateRoute";

export default function WishlistPage() {
  const router = useRouter();
  const { user } = useAuth();
  
  const [wishlistItems, setWishlistItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWishlist = async () => {
      try {
        // Fetch raw wishlist mapping
        const wishlistRes = await api.get("wishlist/");
        
        // Fetch all courses to populate data
        const coursesRes = await api.get("courses/");
        
        // Join the data
        const populatedWishlist = wishlistRes.data.map(item => {
           const courseDetails = coursesRes.data.find(c => c.id === item.course);
           return {
               wishlistId: item.id,
               ...courseDetails
           };
        }).filter(item => item.id); // Ensure course wasn't deleted
        
        setWishlistItems(populatedWishlist);
      } catch (err) {
        console.error("Failed to fetch wishlist", err);
      } finally {
        setLoading(false);
      }
    };

    if (user?.role === "student") {
      fetchWishlist();
    }
  }, [user]);

  const handleRemove = async (wishlistId, e) => {
      e.stopPropagation();
      try {
          await api.delete(`wishlist/${wishlistId}/`);
          setWishlistItems(prev => prev.filter(item => item.wishlistId !== wishlistId));
      } catch (err) {
          console.error("Failed to remove from wishlist", err);
      }
  };

  if (loading) {
    return (
      <PrivateRoute>
        <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
          <div className="spinner"></div>
        </div>
      </PrivateRoute>
    );
  }

  return (
    <PrivateRoute>
      <div className="animate-fade-in" style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
        
        <div style={{ marginBottom: "3rem", display: "flex", alignItems: "center", gap: "1rem" }}>
          <Heart size={32} color="rgb(220, 38, 38)" fill="rgb(220, 38, 38)" />
          <div>
            <h1 style={{ fontSize: "2.5rem", color: "var(--text-main)", marginBottom: "0.5rem" }}>
              My Wishlist
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "1.1rem" }}>
              Courses you've saved for later.
            </p>
          </div>
        </div>

        {wishlistItems.length === 0 ? (
          <div className="glass-panel" style={{ padding: "4rem", textAlign: "center" }}>
            <Heart size={48} color="var(--text-muted)" style={{ margin: "0 auto 1.5rem auto", opacity: 0.5 }} />
            <h3 style={{ fontSize: "1.5rem", color: "var(--text-main)", marginBottom: "1rem" }}>
              Your wishlist is empty
            </h3>
            <p style={{ color: "var(--text-muted)", marginBottom: "2rem" }}>
              Explore our dashboard to find courses that interest you.
            </p>
            <button
              onClick={() => router.push("/dashboard")}
              className="btn-primary"
            >
              Browse Courses
            </button>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "2rem" }}>
            {wishlistItems.map((course) => (
              <div
                key={course.wishlistId}
                className="glass-panel"
                style={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  transition: "transform 0.2s, box-shadow 0.2s",
                  cursor: "pointer",
                  overflow: "hidden"
                }}
                onClick={() => router.push(`/course/${course.id}`)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-5px)";
                  e.currentTarget.style.boxShadow = "var(--shadow-lg)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "none";
                  e.currentTarget.style.boxShadow = "var(--shadow-md)";
                }}
              >
                {/* Thumbnail */}
                <div style={{
                    height: "160px",
                    background: "linear-gradient(135deg, #f8fafc, #f1f5f9)",
                    borderBottom: "1px solid var(--border-light)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    position: "relative"
                }}>
                  {course.thumbnail ? (
                    <img src={course.thumbnail} alt={course.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                  ) : (
                    <BookOpen size={48} color="rgba(15, 23, 42, 0.1)" />
                  )}
                  
                  {/* Remove Button Overlay */}
                  <button 
                    onClick={(e) => handleRemove(course.wishlistId, e)}
                    style={{
                        position: "absolute",
                        top: "10px",
                        right: "10px",
                        background: "rgba(255,255,255,0.9)",
                        border: "none",
                        borderRadius: "50%",
                        width: "36px",
                        height: "36px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        cursor: "pointer",
                        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                        color: "var(--error)",
                        transition: "all 0.2s"
                    }}
                    onMouseEnter={e => e.currentTarget.style.transform = "scale(1.1)"}
                    onMouseLeave={e => e.currentTarget.style.transform = "scale(1)"}
                    title="Remove from wishlist"
                  >
                      <Trash2 size={18} />
                  </button>
                </div>

                <div style={{ padding: "1.5rem", flex: 1, display: "flex", flexDirection: "column" }}>
                  <h3 style={{ fontSize: "1.25rem", marginBottom: "0.25rem", color: "var(--text-main)" }}>
                    {course.title}
                  </h3>
                  <div style={{ fontSize: "0.8rem", color: "var(--accent-primary)", fontWeight: "600", marginBottom: "0.75rem" }}>
                    By {course.instructor_name}
                  </div>
                  <p style={{
                      fontSize: "0.875rem",
                      color: "var(--text-muted)",
                      lineHeight: "1.5",
                      display: "-webkit-box",
                      WebkitLineClamp: "2",
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                  }}>
                    {course.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PrivateRoute>
  );
}
