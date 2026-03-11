"use client";

import { useAuth } from "@/context/AuthContext";
import { usePathname } from "next/navigation";
import Navbar from "@/components/Navbar";
import Sidebar from "@/components/Sidebar";

const PUBLIC_ROUTES = ["/", "/login", "/signup"];

export default function AppShell({ children }) {
  const { user } = useAuth();
  const pathname = usePathname();

  const isPublic = PUBLIC_ROUTES.includes(pathname);
  const showSidebar = !!user && !isPublic;

  return (
    <>
      <Navbar />
      {showSidebar && <Sidebar />}
      <div className={`app-body ${showSidebar ? "has-sidebar" : ""}`}>
        <main>{children}</main>
      </div>
    </>
  );
}
