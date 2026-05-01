import type { Metadata } from "next";
import { Inter_Tight, JetBrains_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const interTight = Inter_Tight({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter-tight",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains-mono",
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Resonantia — Agentic OS for Lab Informatics",
  description:
    "AI-powered plate mapping, dose-response analysis, and sample tracking for lab scientists. Design worklists for Echo, Hamilton, and Opentrons. Fit IC50 curves, normalize plates, browse microscopy images, and manage reagent inventory.",
  keywords: [
    "lab informatics",
    "LIMS",
    "laboratory automation",
    "AI agents",
    "plate mapping",
    "microscopy",
    "data analysis",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${interTight.variable} ${jetbrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans bg-bg text-ink">
        <ClerkProvider>
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
