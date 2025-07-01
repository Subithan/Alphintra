import { redirect } from 'next/navigation';
import { LandingPage } from '@/components/landing/landing-page';

export default function HomePage() {
  // For now, show landing page. In production, you might want to redirect authenticated users
  // Uncomment the line below when authentication is implemented
  // redirect('/dashboard');
  
  return <LandingPage />;
}