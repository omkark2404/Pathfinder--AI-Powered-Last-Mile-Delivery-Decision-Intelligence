'use client';

import { useEffect, useState } from 'react';
import { fetchHealth, HealthInfo } from '@/lib/api';

/** Backend /health info, or null while loading; `error` is true when the API is unreachable. */
export function useHealth(): { health: HealthInfo | null; error: boolean } {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => setError(true));
  }, []);

  return { health, error };
}
