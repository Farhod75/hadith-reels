import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin', 'cyrillic'] })

export const metadata: Metadata = {
  title: 'Hadith Reels — Authentic Islamic Short Reels',
  description:
    'Watch authentic sahih hadith stories as short animated reels. Adults and Kids versions. Arabic, Uzbek, Russian, English narration. Powered by verified Islamic sources.',
  keywords: [
    'hadith reels', 'islamic videos', 'authentic hadith', 'sahih hadith',
    'islamic short videos', 'hadith stories', 'uzbek hadith', 'arabic hadith',
  ],
  authors: [{ name: 'Farhod Elbekov', url: 'https://github.com/Farhod75' }],
  openGraph: {
    title: 'Hadith Reels — Authentic Islamic Short Reels',
    description: 'Sahih hadith stories as short animated reels for Adults and Kids.',
    url: 'https://hadithreels.com',
    siteName: 'Hadith Reels',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Hadith Reels',
    description: 'Authentic hadith as short animated reels · Adults & Kids',
  },
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#1e1b4b',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
  <html lang="en" suppressHydrationWarning>
    <body className={inter.className} suppressHydrationWarning>
      {children}
    </body>
  </html>
)
}
