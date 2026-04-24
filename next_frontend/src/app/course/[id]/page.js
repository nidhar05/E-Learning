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
  AlertCircle,
  Video,
  Heart,
  QrCode,
  CreditCard,
  X
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
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState("qr");
  const [paymentReference, setPaymentReference] = useState("");
  const [paymentConfirmed, setPaymentConfirmed] = useState(false);
  const [razorpayReady, setRazorpayReady] = useState(false);
  const [enrollError, setEnrollError] = useState("");
  const [paymentError, setPaymentError] = useState("");
  const gatewayUnavailable =
    paymentError.toLowerCase().includes("not configured") ||
    paymentError.toLowerCase().includes("not installed");

  const isSubscriptionCourse = course?.access_type === "subscription";
  const accessLabel = isSubscriptionCourse ? "Subscription" : "Free";
  const subscriptionAmount = Number(course?.amount || 0);
  const paymentAccount = process.env.NEXT_PUBLIC_UPI_ID || "nidhusiva05@oksbi";
  const qrPaymentData = `upi://pay?pa=${paymentAccount}&pn=E-Learning&tn=${course?.title || "Course Subscription"}${isSubscriptionCourse ? `&am=${subscriptionAmount.toFixed(2)}&cu=INR` : ""}`;
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(qrPaymentData)}`;

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

  useEffect(() => {
    if (!isSubscriptionCourse) {
      return;
    }

    const existingScript = document.querySelector("script[data-payment='razorpay-checkout']");
    if (existingScript) {
      setRazorpayReady(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.async = true;
    script.dataset.payment = "razorpay-checkout";
    script.onload = () => setRazorpayReady(true);
    script.onerror = () => setPaymentError("Failed to load payment gateway. Check your connection.");
    document.body.appendChild(script);
  }, [isSubscriptionCourse]);

  const completeEnrollment = async () => {
    setEnrollError("");
    setPaymentError("");
    setEnrollLoading(true);
    try {
      await api.post(`enrollments/enroll/${id}/`, {});
      setIsEnrolled(true);
      setPaymentOpen(false);
    } catch (err) {
      console.error(err);
      const message =
        err?.response?.data?.error ||
        err?.response?.data?.message ||
        "Enrollment failed. Complete payment first and try again.";
      setEnrollError(message);
    } finally {
      setEnrollLoading(false);
    }
  };

  const confirmQrPaymentAndEnroll = async () => {
    setPaymentError("");
    setEnrollLoading(true);
    try {
      if (!paymentConfirmed) {
        throw new Error("Please confirm that payment is completed.");
      }
      if (!paymentReference.trim() || paymentReference.trim().length < 6) {
        throw new Error("Enter valid UTR / transaction reference (minimum 6 characters).");
      }

      await api.post(`enrollments/enroll/${id}/`, {
        payment_method: "qr",
        payment_reference: paymentReference.trim(),
        payment_confirmed: true,
      });

      setIsEnrolled(true);
      setPaymentOpen(false);
      setPaymentReference("");
      setPaymentConfirmed(false);
    } catch (err) {
      const message =
        err?.response?.data?.error ||
        err?.message ||
        "QR payment confirmation failed. Try again.";
      setPaymentError(message);
    } finally {
      setEnrollLoading(false);
    }
  };

  const initiateSubscriptionPayment = async () => {
    setPaymentError("");
    setEnrollLoading(true);

    try {
      if (!razorpayReady || typeof window === "undefined" || !window.Razorpay) {
        throw new Error("Payment gateway is not ready yet. Please try again.");
      }

      const createOrderResponse = await api.post(
        `enrollments/payments/create-order/${id}/`,
        { payment_method: paymentMethod },
      );

      if (createOrderResponse.data?.message === "Already enrolled") {
        setIsEnrolled(true);
        setPaymentOpen(false);
        return;
      }

      const orderPayload = createOrderResponse.data;
      const enabledMethods = paymentMethod === "qr"
        ? { upi: true, card: false, netbanking: false, wallet: false, emi: false, paylater: false }
        : { upi: false, card: true, netbanking: false, wallet: false, emi: false, paylater: false };

      const options = {
        key: orderPayload.razorpay_key_id,
        amount: orderPayload.amount,
        currency: orderPayload.currency || "INR",
        name: "E-Learning",
        description: `Subscription for ${orderPayload.course_title || course?.title || "Course"}`,
        order_id: orderPayload.order_id,
        method: enabledMethods,
        prefill: {
          name: user?.username || "",
        },
        notes: {
          course_id: String(id),
          payment_method: paymentMethod,
        },
        theme: {
          color: "#f97316",
        },
        handler: async function (response) {
          try {
            await api.post(`enrollments/payments/verify/${id}/`, {
              payment_method: paymentMethod,
              razorpay_order_id: response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature,
            });
            setIsEnrolled(true);
            setPaymentOpen(false);
          } catch (verificationError) {
            const verificationMessage =
              verificationError?.response?.data?.error ||
              "Payment succeeded but verification failed. Contact support.";
            setPaymentError(verificationMessage);
          }
        },
        modal: {
          ondismiss: () => {
            setEnrollLoading(false);
          },
        },
      };

      const razorpayCheckout = new window.Razorpay(options);
      razorpayCheckout.open();
    } catch (err) {
      console.error(err);
      const message =
        err?.response?.data?.error ||
        err?.message ||
        "Unable to start payment. Please try again.";
      setPaymentError(message);
    } finally {
      setEnrollLoading(false);
    }
  };

  const handleEnroll = async () => {
    if (isSubscriptionCourse && subscriptionAmount <= 0) {
      setEnrollError("Subscription amount is not configured by instructor.");
      return;
    }

    if (isSubscriptionCourse) {
      setPaymentError("");
      setPaymentOpen(true);
      return;
    }

    await completeEnrollment();
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
              <div
                style={{
                  width: "fit-content",
                  marginBottom: "1rem",
                  padding: "0.35rem 0.85rem",
                  borderRadius: "999px",
                  background: "rgba(249, 115, 22, 0.12)",
                  color: "var(--accent-primary)",
                  fontSize: "0.85rem",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  letterSpacing: "0",
                }}
              >
                {accessLabel}
              </div>
              {isSubscriptionCourse && subscriptionAmount > 0 && (
                <div style={{ color: "var(--text-main)", fontWeight: "700", marginBottom: "1rem" }}>
                  Price: ₹{subscriptionAmount.toFixed(2)}
                </div>
              )}
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
                <>
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
                    {enrollLoading ? "Enrolling..." : isSubscriptionCourse ? "Pay and Enroll" : "Enroll Now"}
                  </button>
                  {enrollError && (
                    <div
                      style={{
                        marginTop: "0.85rem",
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        color: "#b91c1c",
                        background: "#fef2f2",
                        border: "1px solid #fecaca",
                        padding: "0.65rem 0.85rem",
                        borderRadius: "8px",
                        width: "fit-content",
                      }}
                    >
                      <AlertCircle size={16} /> {enrollError}
                    </div>
                  )}
                </>
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
        {paymentOpen && (
          <div
            onClick={() => setPaymentOpen(false)}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(15, 23, 42, 0.45)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "1.5rem",
              zIndex: 80,
            }}
          >
            <div
              onClick={(e) => e.stopPropagation()}
              style={{
                width: "100%",
                maxWidth: "520px",
                background: "white",
                borderRadius: "16px",
                padding: "1.5rem",
                boxShadow: "var(--shadow-lg)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", marginBottom: "1rem" }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: "1.35rem" }}>Subscription Payment</h3>
                  <p style={{ marginTop: "0.35rem", color: "var(--text-muted)" }}>
                    Complete payment to enroll in {course.title}.
                  </p>
                  {subscriptionAmount > 0 && (
                    <p style={{ marginTop: "0.35rem", color: "var(--accent-primary)", fontWeight: 700 }}>
                      Payable amount: ₹{subscriptionAmount.toFixed(2)}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => setPaymentOpen(false)}
                  style={{
                    border: "none",
                    background: "transparent",
                    cursor: "pointer",
                    color: "var(--text-muted)",
                    height: "32px",
                  }}
                >
                  <X size={20} />
                </button>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.25rem" }}>
                <button
                  type="button"
                  onClick={() => {
                    setPaymentMethod("qr");
                    setPaymentError("");
                  }}
                  style={{
                    padding: "0.9rem",
                    borderRadius: "10px",
                    border: paymentMethod === "qr" ? "2px solid var(--accent-primary)" : "1px solid var(--border-light)",
                    background: paymentMethod === "qr" ? "rgba(249, 115, 22, 0.08)" : "white",
                    color: "var(--text-main)",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.5rem",
                  }}
                >
                  <QrCode size={18} /> QR Scan
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPaymentMethod("card");
                    setPaymentError("");
                  }}
                  style={{
                    padding: "0.9rem",
                    borderRadius: "10px",
                    border: paymentMethod === "card" ? "2px solid var(--accent-primary)" : "1px solid var(--border-light)",
                    background: paymentMethod === "card" ? "rgba(249, 115, 22, 0.08)" : "white",
                    color: "var(--text-main)",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "0.5rem",
                  }}
                >
                  <CreditCard size={18} /> Card
                </button>
              </div>

              <div
                style={{
                  marginBottom: "1.25rem",
                  border: "1px solid var(--border-light)",
                  borderRadius: "12px",
                  padding: "0.9rem 1rem",
                  background: "#f8fafc",
                  color: "var(--text-muted)",
                }}
              >
                {paymentMethod === "qr"
                  ? "Scan this QR in any UPI app. Amount and receiver are auto-filled."
                  : "Card checkout opens in secure Razorpay gateway. Enter card details there."}
                <div style={{ marginTop: "0.45rem", color: "var(--accent-primary)", fontWeight: 700 }}>
                  Receiver UPI: {paymentAccount}
                </div>
              </div>

              {paymentMethod === "qr" && (
                <div style={{ marginBottom: "1rem" }}>
                  <div
                    role="img"
                    aria-label="UPI payment QR code"
                    style={{
                      width: "220px",
                      height: "220px",
                      margin: "0 auto 0.75rem",
                      borderRadius: "12px",
                      border: "1px solid var(--border-light)",
                      background: "white",
                      backgroundImage: `url(${qrCodeUrl})`,
                      backgroundPosition: "center",
                      backgroundSize: "200px 200px",
                      backgroundRepeat: "no-repeat",
                    }}
                  />
                  <div style={{ display: "grid", gap: "0.65rem" }}>
                    <input
                      placeholder="Enter UTR / transaction reference"
                      value={paymentReference}
                      onChange={(e) => setPaymentReference(e.target.value)}
                    />
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        color: "var(--text-main)",
                        fontSize: "0.92rem",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={paymentConfirmed}
                        onChange={(e) => setPaymentConfirmed(e.target.checked)}
                      />
                      I completed payment to this UPI ID.
                    </label>
                  </div>
                </div>
              )}

              {paymentError && (
                <div
                  style={{
                    marginBottom: "0.9rem",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                    color: "#b91c1c",
                    background: "#fef2f2",
                    border: "1px solid #fecaca",
                    padding: "0.65rem 0.85rem",
                    borderRadius: "8px",
                  }}
                >
                  <AlertCircle size={16} /> {paymentError}
                </div>
              )}
              {paymentMethod === "card" && gatewayUnavailable && (
                <div
                  style={{
                    marginBottom: "0.9rem",
                    color: "var(--text-muted)",
                    fontSize: "0.9rem",
                    lineHeight: 1.45,
                  }}
                >
                  Admin setup needed: add `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in backend `.env`, then restart Django server.
                </div>
              )}

              <button
                type="button"
                className="btn-primary"
                disabled={
                  enrollLoading ||
                  (paymentMethod === "card" && (!razorpayReady || gatewayUnavailable))
                }
                onClick={paymentMethod === "qr" ? confirmQrPaymentAndEnroll : initiateSubscriptionPayment}
                style={{ width: "100%", padding: "0.85rem 1rem" }}
              >
                {enrollLoading
                  ? "Processing..."
                  : paymentMethod === "card" && gatewayUnavailable
                    ? "Gateway Setup Required"
                    : paymentMethod === "card" && !razorpayReady
                      ? "Loading Payment Gateway..."
                      : paymentMethod === "qr"
                        ? "I Paid via UPI, Enroll Me"
                        : "Pay Securely and Enroll"}
              </button>
            </div>
          </div>
        )}
      </div>
    </PrivateRoute>
  );
}
