import './globals.css';
import Sidebar from '@/components/Sidebar';

export const metadata = {
  title: 'Pathfinder--AI-Powered-Last-Mile-Delivery-Decision-Intelligence',
  description: 'Logistics Decision Intelligence Platform for ETA Prediction, Route Optimization, Risk Scoring & What-If Simulation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-[#090d16] text-slate-100 min-h-screen flex antialiased">
        <Sidebar />
        <main className="flex-1 ml-64 min-h-screen overflow-x-hidden">
          {children}
        </main>
      </body>
    </html>
  );
}
