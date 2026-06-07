"use client";

import { useAuth } from "@/contexts/AuthContext";

export function useCurrentUser() {
  const { user, isLoading } = useAuth();
  
  return {
    user,
    isLoading,
    isAdmin: user?.role === "ADMIN",
    isViewer: user?.role === "VIEWER",
  };
}
