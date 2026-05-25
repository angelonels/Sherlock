import type { Metadata } from "next";
import { AppProviders } from "@/features/providers/app-providers";
import { SherlockClerkProvider } from "@/features/providers/clerk-provider";
import "./globals.css";

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
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <SherlockClerkProvider>
          <AppProviders>{children}</AppProviders>
        </SherlockClerkProvider>
      </body>
    </html>
  );
}
