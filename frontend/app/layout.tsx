import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "SynapVault Dashboard",
  description: "Enterprise Knowledge Network & Security Vault",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full`}>
      <body className="h-full bg-zinc-950 text-zinc-100 antialiased font-sans flex overflow-hidden">

        {/* SIDEBAR */}
        <aside className="w-64 border-r border-zinc-800 bg-zinc-900/50 flex flex-col justify-between hidden md:flex">
          <div>
            {/* Branding */}
            <div className="h-16 flex items-center px-6 border-b border-zinc-800">
              <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent tracking-tight">
                SynapVault
              </span>
            </div>

            {/* Navigation Links */}
            <nav className="p-4 space-y-1">
              <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg bg-zinc-800 text-zinc-50 font-medium text-sm transition">
                <span>📊</span> Dashboard
              </a>
              <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50 font-medium text-sm transition">
                <span>📁</span> Document Ingestion
              </a>
              <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50 font-medium text-sm transition">
                <span>💬</span> Neural Chat
              </a>
              <a href="#" className="flex items-center gap-3 px-3 py-2 rounded-lg text-zinc-400 hover:text-zinc-50 hover:bg-zinc-800/50 font-medium text-sm transition">
                <span>⚙️</span> Settings
              </a>
            </nav>
          </div>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-zinc-800 flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-sm">
              JD
            </div>
            <div>
              <p className="text-sm font-medium">John Doe</p>
              <p className="text-xs text-zinc-500">Enterprise Admin</p>
            </div>
          </div>
        </aside>

        {/* MAIN CONTAINER */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

          {/* NAVBAR / HEADER */}
          <header className="h-16 border-b border-zinc-800 bg-zinc-900/20 backdrop-blur-md flex items-center justify-between px-6 z-10">
            <h1 className="text-lg font-semibold tracking-tight text-zinc-200">System Control Center</h1>
            <div className="flex items-center gap-4">
              {/* API Status Badge */}
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900 border border-zinc-800 text-xs">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span className="text-zinc-400">Environment: Dev</span>
              </div>
            </div>
          </header>

          {/* PAGE CONTENT */}
          <main className="flex-1 overflow-y-auto p-6 md:p-8">
            <div className="max-w-5xl mx-auto">
              {children}
            </div>
          </main>
        </div>

      </body>
    </html>
  );
}
