// src/app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Ace Portfolio Intelligence",
  description: "Ace Ventures analytics UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#161616] text-[#f4f4f4]">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
