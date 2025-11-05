// File Path: app/layout.tsx
// Description: This file defines the root layout for the entire Next.js application.
// It sets up the basic HTML structure, loads global styles, and provides a template for all pages.
// Dependencies:
// - app/globals.css: For global application styles.
// - Next.js: For core framework functionalities (React, metadata).
// Dependents:
// - All page.tsx files in the application will be wrapped by this layout.

import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css"; // Import global styles

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// --- Metadata Configuration ---
// Defines the default metadata for the application (e.g., title, description).
// This can be overridden by individual pages.
export const metadata: Metadata = {
  title: "Anything Agents Frontend",
  description: "A modern frontend for interacting with Anything Agents API.",
};

// --- RootLayout Component ---
// This is the main layout component that wraps all page content.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* children represents the content of the currently active page or nested layout */}
        {children}
      </body>
    </html>
  );
}
