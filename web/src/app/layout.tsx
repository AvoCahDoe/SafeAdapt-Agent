import type { Metadata } from "next";
import { Fraunces, Source_Sans_3 } from "next/font/google";
import { SiteNav } from "@/components/SiteNav";
import "./globals.css";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
});

const sourceSans = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-source",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SafeAdapt — Alignment drift research",
  description:
    "Public showcase for SafeAdapt: studying alignment drift in continually interacting LLM agents.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${fraunces.variable} ${sourceSans.variable}`}>
        <SiteNav />
        {children}
        <footer className="site-footer">
          SafeAdapt research prototype ·{" "}
          <a
            href="https://github.com/AvoCahDoe/SafeAdapt-Agent"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </footer>
      </body>
    </html>
  );
}
