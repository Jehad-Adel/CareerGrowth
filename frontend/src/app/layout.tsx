import type { Metadata } from "next";
import { Fraunces, Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  axes: ["opsz", "SOFT"],
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

const TITLE = "CareerGrowth — grow your career like a farm";
const DESCRIPTION =
  "Upload your CV once. Match it against real jobs, see exactly what to learn next, " +
  "and watch your skills grow into a farm that reflects what you actually did.";

export const metadata: Metadata = {
  // Makes every relative OG/Twitter image URL absolute, which crawlers require.
  metadataBase: new URL(SITE_URL),
  title: { default: TITLE, template: "%s · CareerGrowth" },
  description: DESCRIPTION,
  applicationName: "CareerGrowth",
  openGraph: {
    type: "website",
    siteName: "CareerGrowth",
    title: TITLE,
    description: DESCRIPTION,
    url: SITE_URL,
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
