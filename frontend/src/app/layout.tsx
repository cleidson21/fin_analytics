import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";
import { AuthProvider } from "@/contexts/AuthContext";
import { RechartsConsoleWarningFix } from "@/components/providers/RechartsConsoleWarningFix";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { THEME_BOOTSTRAP_SCRIPT } from "@/lib/theme";

const inter = Inter({
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "FinAnalytics",
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
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP_SCRIPT }} />
      </head>
      <body className="min-h-full bg-background text-foreground">
        <ThemeProvider>
          <AuthProvider>
            <RechartsConsoleWarningFix />
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
