import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider } from "@/contexts/AuthContext";
import { RechartsConsoleWarningFix } from "@/components/providers/RechartsConsoleWarningFix";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Wealth OS",
  description: "Motor Financeiro Privado",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${inter.className} h-full antialiased`}
    >
      <body className="min-h-full bg-zinc-950 text-zinc-50">
        <AuthProvider>
          <RechartsConsoleWarningFix />
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}
