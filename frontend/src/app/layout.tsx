"use client";
import type { Metadata } from "next";
import { PostHogProvider } from '@posthog/react';
import "@/styles/tokens.css";
import "@/styles/utils.css";
import "./globals.css";

// export const metadata: Metadata = {
//   title: "Stories - Search insightful podcast stories",
//   description: "Search for insightful stories across thousands of podcast conversations. Ask questions and discover top creator insights.",
// };

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <PostHogProvider
          apiKey={process.env.NEXT_PUBLIC_POSTHOG_KEY || ''}
          options={{
            api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST,
          }}
        >
          {children}
        </PostHogProvider>
      </body>
    </html>
  );
}
