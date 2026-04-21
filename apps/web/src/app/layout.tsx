import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SherlockClerkProvider } from "@/features/providers/clerk-provider";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sherlock | AI Data Analyst",
  description:
    "Upload tabular data, ask questions, and get evidence-backed analysis with charts, tables, and data-quality warnings.",
  openGraph: {
    title: "Sherlock | AI Data Analyst",
    description:
      "Investigate CSV and Excel files with evidence-backed findings, charts, tables, KPI cards, and data-quality warnings.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <SherlockClerkProvider>{children}</SherlockClerkProvider>
      </body>
    </html>
  );
}
