import '../styles/dashboard.css';
//Components
import Navbar from '../ui/navbar';
//import Link from 'next/link';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <Navbar />
      {children}
    </div>
  );
}
