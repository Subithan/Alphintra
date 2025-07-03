import { Navbar } from "../components/landing/Navbar";
import { Hero } from "../components/landing/Hero";
import { Features } from "../components/landing/Features";
import { FAQ } from "../components/landing/FAQ";
import { CallToAction } from "../components/landing/CallToAction";
import { Footer } from "../components/landing/Footer";
import React from "react";

export default function HomePage() {
  return (
    <>
      <Navbar />
      <Hero />
      <Features />
      <FAQ />
      <CallToAction />
      <Footer />
    </>
  );
}