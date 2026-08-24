import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'The Codebase Archaeologist 🏛️',
  description: 'Deep RAG & Vector Search Engine for Git Repositories',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-sky-500 selection:text-white">
        {children}
      </body>
    </html>
  )
}
