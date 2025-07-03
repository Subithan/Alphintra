import { Navbar } from "@/components/Navbar";
import { Hero } from "@/components/Hero";
import { LogoTicker } from "@/components/LogoTicker";
import { Features } from "@/components/Features";
import { Strategies } from "@/components/Strategies";
import { FAQs } from "@/components/FAQs";
import { CallToAction } from "@/components/CallToAction";
import { Footer } from "@/components/Footer";
import React from "react"; // Import React for JSX in TypeScript

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <LogoTicker />
      <section id="features">
        <Features />
      </section>
      <section id="strategies">
        <Strategies />
      </section>
      <section id="faq">
        <FAQs />
      </section>
      <section id="updates">
        <CallToAction />
      </section>
      <Footer />
    </>
  );
}