import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Study Buddy Dashboard",
  description: "Advanced Agentic Coding Interface",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} flex h-screen w-screen overflow-hidden`}>
        <Sidebar />
        <main className="flex-1 h-full overflow-y-auto bg-background p-8">
          {children}
        </main>
      </body>
    </html>
  );
}
