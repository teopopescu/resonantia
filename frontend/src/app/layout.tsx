import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-playfair",
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
      className={`${inter.variable} ${playfair.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans bg-cream text-charcoal">
        <ClerkProvider>
          {children}
        </ClerkProvider>
      </body>
    </html>
  );
}
