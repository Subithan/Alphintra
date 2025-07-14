"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";

export default function Dashboard() {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true); // ensures client-side rendering only
  }, []);

  if (!mounted) return null; // prevent rendering until after hydration

  return (
<div></div>
  );
}
