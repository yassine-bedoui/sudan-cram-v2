import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sudan CRAM v2.0",
  description: "Conflict Risk Assessment & Monitoring System for Sudan",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
