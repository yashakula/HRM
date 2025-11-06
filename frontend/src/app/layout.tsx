import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/layout/Providers";
import AuthChecker from "@/components/auth/AuthChecker";
import Navbar from "@/components/layout/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "HRM System",
  description: "Human Resource Management System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>
          <AuthChecker>
            <div className="relative flex min-h-screen flex-col">
              <Navbar />
              <div className="flex-1">
                <main className="container mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                  {children}
                </main>
              </div>
            </div>
          </AuthChecker>
        </Providers>
      </body>
    </html>
  );
}
