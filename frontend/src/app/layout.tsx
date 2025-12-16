"use client";
import type { Metadata } from "next";
import { Urbanist } from 'next/font/google';
import { PostHogProvider } from '@posthog/react';
import "@/styles/tokens.css";
import "@/styles/utils.css";
import "./globals.css";

// Configure Urbanist font
const urbanist = Urbanist({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700', '800', '900'],
  style: ['normal', 'italic'],
  display: 'swap',
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <title>Stories - Search insightful podcast stories</title>
        <meta name="description" content="Search for insightful stories across thousands of podcast conversations. Ask questions and discover top creator insights." />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className={urbanist.className}>
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
