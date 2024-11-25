// app/dashboard/page.tsx
'use client';

import { useState, useEffect } from 'react';

export default function DashboardPage() {
  const [userData, setUserData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/user');
        if (!response.ok) {
          throw new Error('Failed to load user data');
        }
        const data = await response.json();
        setUserData(data);
      } catch (err) {
        setError((err as Error).message);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="dashboard-container">
      <h1>Welcome to F1 Gachas!</h1>
      {error && <p className="error">{error}</p>}
      {userData ? (
        <div>
          <p>User Info:</p>
          <pre>{JSON.stringify(userData, null, 2)}</pre>
        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
}
