import { useTheme as useNextTheme } from 'next-themes';
import { useEffect, useState } from 'react';

export const useTheme = () => {
  const { theme, resolvedTheme } = useNextTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  // Return light theme during SSR to prevent hydration issues
  if (!mounted) {
    return { theme: 'light' };
  }

  // Use resolvedTheme to get the actual theme (handles 'system' preference)
  return { theme: resolvedTheme || 'light' };
};