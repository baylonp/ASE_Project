// app/layout.tsx
import './styles/globals.css';

export const metadata = {
  title: 'F1 Gachas',
  description: 'Collect and trade F1 gachas!',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <main>{children}</main>
      </body>
    </html>
  );
}
