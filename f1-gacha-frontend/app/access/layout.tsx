// app/access/layout.tsx
import Image from 'next/image';
import '../styles/login.css';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="login-grid">
      {/* Left Section: Image */}
      <div>
        <Image
          src="/f1-gachas-red.png"
          alt="Description of image"
          width={500}
          height={300}
          priority
          className="image-f1"
        />
      </div>
      {/* Right Section: Forms */}
      <div className="w-1/2 p-8">{children}</div>
    </div>
  );
}
