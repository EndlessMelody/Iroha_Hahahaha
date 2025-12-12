import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Iroha Study Buddy",
  description: "Chat with Isshiki Iroha — your cute AI study mentor ✨",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Mali:wght@400;500;600;700&family=Pacifico&family=Patrick+Hand&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-paper-cream text-ink-primary">{children}</body>
    </html>
  );
}
