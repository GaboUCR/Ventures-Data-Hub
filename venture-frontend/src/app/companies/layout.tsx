// src/app/companies/layout.tsx
"use client";

import { RequireAuth } from "@/components/auth/RequireAuth";

export default function CompaniesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <RequireAuth>{children}</RequireAuth>;
}
