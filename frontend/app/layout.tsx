import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ollive — LLM Inference Logger",
  description: "Chatbot with inference logging",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="h-full">{children}</body>
    </html>
  );
}