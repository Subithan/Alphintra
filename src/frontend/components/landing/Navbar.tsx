"use client";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import React from "react";
import LogoIcon from "@/components/ui/LogoIcon";
import { motion, AnimatePresence } from "framer-motion";

export const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState<boolean>(false);
  const [hovered, setHovered] = useState<string | null>(null);
  const [activeHash, setActiveHash] = useState<string>("#about");
  const [isScrolled, setIsScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  const toggleMenu = () => setIsMenuOpen((v) => !v);
  const handleNavClick = () => setIsMenuOpen(false);
  const handleNavItemClick = (href: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
    handleNavClick();
    if (href === "#about") {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
      try { history.replaceState(null, "", "#about"); } catch {}
    }
  };

  // Scroll state + progress bar
  useEffect(() => {
    const update = () => {
      const doc = document.documentElement;
      const height = Math.max(1, doc.scrollHeight - window.innerHeight);
      const p = Math.min(1, Math.max(0, window.scrollY / height));
      setScrollProgress(p);
      setIsScrolled(window.scrollY > 8);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", update as any);
      window.removeEventListener("resize", update as any);
    };
  }, []);

  // Active section highlight via IntersectionObserver with hash fallback
  useEffect(() => {
    const ids = ["features", "faq", "updates"]; // observed sections
    const elements = ids
      .map((id) => document.getElementById(id))
      .filter(Boolean) as HTMLElement[];

    const setTopFallback = () => {
      if (window.scrollY < 120) setActiveHash("#about");
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
        if (visible[0]) {
          setActiveHash(`#${(visible[0].target as HTMLElement).id}`);
        } else {
          setTopFallback();
        }
      },
      { root: null, rootMargin: "-20% 0px -55% 0px", threshold: [0.2, 0.35, 0.6] }
    );

    elements.forEach((el) => observer.observe(el));

    const onHash = () => setActiveHash(window.location.hash || "#about");
    window.addEventListener("hashchange", onHash);
    setTopFallback();

    return () => {
      observer.disconnect();
      window.removeEventListener("hashchange", onHash);
    };
  }, []);

  interface NavItem {
    label: string;
    href: string;
  }

  const navItems: NavItem[] = useMemo(
    () => [
      { label: "About", href: "#about" },
      { label: "Features", href: "#features" },
      { label: "FAQ", href: "#faq" },
      { label: "Updates", href: "#updates" },
    ],
    []
  );

  const containerClasses = isScrolled
    ? "bg-black/65 backdrop-blur-xl border-white/15 shadow-[0_6px_30px_rgba(0,0,0,0.35)]"
    : "bg-black/40 backdrop-blur-xl border-white/10";

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className={`${containerClasses} border-b`}>        
        <div className="mx-auto max-w-[120rem] px-4 sm:px-6 lg:px-8">
          <div className="py-3 sm:py-4 flex items-center justify-between">
            <Link href="/" aria-label="Homepage" className="flex items-center gap-3">
              <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-2xl bg-gradient-to-br from-yellow-400 to-amber-500 p-[2px]">
                <div className="h-full w-full rounded-2xl bg-black/90 grid place-items-center">
                  <LogoIcon className="text-white/95 w-6 h-6 sm:w-7 sm:h-7" />
                </div>
              </div>
              <span className="text-white font-extrabold text-lg sm:text-xl tracking-wide">
                ALPHINTRA
              </span>
            </Link>

            <button
              aria-label="Toggle Menu"
              className="text-white/90 border border-white/20 h-10 w-10 inline-flex justify-center items-center rounded-xl lg:hidden bg-white/5 hover:bg-white/10 transition"
              onClick={toggleMenu}
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>

            <nav className="hidden lg:flex items-center gap-10">
              {navItems.map((item) => {
                const isActive = activeHash === item.href;
                return (
                  <Link
                    key={item.label}
                    href={item.href}
                    onClick={handleNavItemClick(item.href)}
                    onMouseEnter={() => setHovered(item.label)}
                    onMouseLeave={() => setHovered(null)}
                    className="relative text-sm font-medium text-white/70 hover:text-white transition px-1 py-1"
                    scroll
                  >
                    <span className="relative z-10">{item.label}</span>
                    {(hovered === item.label || isActive) && (
                      <motion.span
                        layoutId="nav-underline"
                        className="absolute inset-x-0 -bottom-1 h-[2px] bg-gradient-to-r from-yellow-400 via-amber-400 to-yellow-300 rounded-full"
                        transition={{ type: "spring", stiffness: 500, damping: 40, mass: 0.6 }}
                      />
                    )}
                  </Link>
                );
              })}

              <div className="h-6 w-px bg-white/10" />

              <div className="flex items-center gap-3">
                <Link
                  href="/auth"
                  className="relative inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold text-yellow-100 hover:text-white transition"
                >
                  <span className="absolute inset-0 rounded-xl ring-1 ring-yellow-300/30" aria-hidden />
                  <span className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/5 to-white/0 opacity-60" aria-hidden />
                  Log In
                </Link>
                <Link
                  href="/auth"
                  className="relative inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold text-slate-900"
                >
                  <span
                    className="absolute inset-0 rounded-xl bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500"
                    aria-hidden
                  />
                  <span className="absolute inset-0 rounded-xl blur-md opacity-60 bg-yellow-300/50" aria-hidden />
                  <span className="relative">Get for Free</span>
                </Link>
              </div>
            </nav>
          </div>
          {/* Mobile Menu */}
          <AnimatePresence>
            {isMenuOpen && (
              <motion.nav
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.18, ease: "easeOut" }}
                className="lg:hidden mb-3 overflow-hidden"
              >
                <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-4">
                  <div className="flex flex-col gap-2">
                    {navItems.map((item) => (
                      <Link
                        key={item.label}
                        href={item.href}
                        className="relative rounded-xl px-3 py-2 text-white/80 hover:text-white hover:bg-white/5 transition"
                        onClick={handleNavItemClick(item.href)}
                        scroll
                      >
                        {item.label}
                      </Link>
                    ))}
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    <Link
                      href="/auth"
                      className="relative inline-flex items-center justify-center rounded-xl px-3 py-2 text-sm font-semibold text-yellow-100 hover:text-white transition"
                      onClick={handleNavClick}
                    >
                      <span className="absolute inset-0 rounded-xl ring-1 ring-yellow-300/30" aria-hidden />
                      <span className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/5 to-white/0 opacity-60" aria-hidden />
                      Log In
                    </Link>
                    <Link
                      href="/auth"
                      className="relative inline-flex items-center justify-center rounded-xl px-3 py-2 text-sm font-semibold text-slate-900"
                      onClick={handleNavClick}
                    >
                      <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-yellow-300 via-amber-400 to-yellow-500" aria-hidden />
                      <span className="absolute inset-0 rounded-xl blur-md opacity-60 bg-yellow-300/50" aria-hidden />
                      <span className="relative">Get for Free</span>
                    </Link>
                  </div>
                </div>
              </motion.nav>
            )}
          </AnimatePresence>
          {/* Scroll progress bar */}
          <div className="relative h-[2px]">
            <div className="absolute inset-x-0 bottom-0 h-px bg-white/10" />
            <motion.div
              className="absolute left-0 bottom-0 h-[2px] rounded-full"
              style={{ background: "linear-gradient(90deg,#FACC15,#F59E0B,#FDE68A)" }}
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(scrollProgress * 100)}%` }}
              transition={{ duration: 0.1, ease: "linear" }}
            />
          </div>
        </div>
      </div>
    </header>
  );
};
