import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Governance Gateway Console",
  description: "Approval queue, audit viewer, and policy playground",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <main>
          <header className="site-header">
            <h1 className="brand">
              AI Governance Gateway
              <span>Admin console</span>
            </h1>
            <nav>
              <Link href="/">Home</Link>
              <Link href="/approvals">Approvals</Link>
              <Link href="/audit">Audit</Link>
              <Link href="/playground">Playground</Link>
            </nav>
          </header>
          {children}
        </main>
      </body>
    </html>
  );
}
