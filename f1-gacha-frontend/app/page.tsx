// app/page.tsx
'use client';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import './styles/landing.css';
import { Button } from '@mui/material';
import LoginSharpIcon from '@mui/icons-material/LoginSharp';

export default function Page() {
  const router = useRouter();
  const handleEnter = () => {
    router.push('/access');
  };
  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Background Video */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover"
      >
        <source src="/f1video.mp4" type="video/mp4" />
        Your browser does not support the video tag.
      </video>
      {/* Hovered Content */}
      <div className="relative z-10 flex items-center justify-center h-full">
        {/* F1 Image */}
        <div className="flex items-center justify-center min-h-screen flex-col">
          <Image
            src="/f1-gachas-red.png"
            alt="Description of image"
            width={500}
            height={300}
            priority
            className="mb-4 shadow-image"
          />
          {/* Enter Button */}
          <Button
            variant="contained"
            sx={{
              backgroundColor: 'red', // Custom button color
              color: 'white', // Text and icon color
              '&:hover': {
                backgroundColor: '#ff9a9a', // Hover state color
              },
            }}
            onClick={handleEnter}
            startIcon={<LoginSharpIcon />} // Adds the icon to the start of the button
          >
            Enter
          </Button>
        </div>
      </div>
    </div>
  );
}
