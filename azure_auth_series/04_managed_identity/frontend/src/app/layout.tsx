import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { MsalProviderWrapper } from "@/components/auth/msal-provider";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Azure Auth — Managed Identity + Key Vault",
  description:
    "Deploy to Azure with Managed Identity and Key Vault — RBAC app on Container Apps + Static Web Apps",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased font-[family-name:var(--font-geist-sans)] flex min-h-screen flex-col`}
      >
        <MsalProviderWrapper>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </MsalProviderWrapper>
      </body>
    </html>
  );
}
