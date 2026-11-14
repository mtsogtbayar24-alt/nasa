import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'COSMIC SHIFT — Infrared Sky Motion Explorer',
  description: 'A research prototype for astronomical time-domain image comparison. Synthetic demo, not official NASA data.',
};

export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en"><body>{children}</body></html>;
}
