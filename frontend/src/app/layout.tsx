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
      <body className={`${inter.className} flex h-screen w-screen overflow-hidden bg-background`}>
        <Sidebar />
        
        {/* 
          md:ml-64 prevents the content from sliding under the desktop sidebar.
          p-4 md:p-8 ensures mobile users aren't crushed by giant margins.
        */}
        <main className="flex-1 h-full overflow-y-auto md:ml-64 p-4 md:p-8 transition-all duration-300">
          {children}
        </main>
      </body>
    </html>
  );
}