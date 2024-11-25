// app/access/layout.tsx
import Image from 'next/image';

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-full max-w-4xl flex shadow-lg rounded-lg overflow-hidden">
        {/* Left Section: Image */}
        <div className="w-1/2 relative">
          <Image
            src="/f1-gachas-red.png"
            alt="Description of image"
            width={500}
            height={300}
            priority
          />
        </div>
        {/* Right Section: Forms */}
        <div className="w-1/2 p-8">{children}</div>
      </div>
    </div>
  );
}
