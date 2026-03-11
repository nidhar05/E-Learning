"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard,
  BookOpen,
  Heart,
  PlusCircle,
  LogOut,
} from "lucide-react";

const NAV_ITEMS = {
  student: [
    { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Wishlist", icon: Heart, href: "/dashboard/wishlist" },
  ],
  instructor: [
    { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
    { label: "Create Course", icon: PlusCircle, href: "/create-course" },
  ],
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  if (!user) return null;

  const items = NAV_ITEMS[user.role] || NAV_ITEMS.student;

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {items.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={`sidebar-item ${isActive ? "active" : ""}`}
              title={item.label}
            >
              <Icon size={20} className="sidebar-icon" />
              <span className="sidebar-label">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <button
          onClick={handleLogout}
          className="sidebar-item sidebar-logout"
          title="Logout"
        >
          <LogOut size={20} className="sidebar-icon" />
          <span className="sidebar-label">Logout</span>
        </button>
      </div>
    </aside>
  );
}
