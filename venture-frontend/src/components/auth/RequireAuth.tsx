// src/components/auth/RequireAuth.tsx
"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !user) {
      // Preserve where the user was trying to go
      const next = encodeURIComponent(pathname);
      router.push(`/auth/login?next=${next}`);
    }
  }, [isLoading, user, router, pathname]);

  if (isLoading || (!user && typeof window !== "undefined")) {
    return <div className="p-6">Checking access…</div>;
  }

  // If server-rendered and no user yet, just render children;
  // client effect will handle redirect if needed.
  return <>{children}</>;
}
