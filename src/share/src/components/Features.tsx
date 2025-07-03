"use client";
import React, { useState } from "react";
import Image from "next/image";

interface Feature {
  icon: string;
  title: string;
  description: string;
}

const features: Feature[] = [
  {
    icon: "/images/graph.svg",
    title: "Automatic Trading",
    description:
      "Cryptotrading is 24/7. So is your bot. Give yourself an edge, and while everyone else sleeps, you’ll never miss a beat.",
  },
  {
    icon: "/images/strategy.svg",
    title: "Custom Strategies",
    description:
      "Create and deploy your own trading strategies tailored to your risk profile and market goals.",
  },
  {
    icon: "/images/analytics.svg",
    title: "Real-Time Analytics",
    description:
      "Gain insights with real-time market data and performance tracking to optimize your trades.",
  },
  {
    icon: "/images/portfolio.svg",
    title: "Backtesting",
    description:
      "Test your strategies on historical data before deploying real capital.",
  },
];

export const Features = () => {
  const [activeIndex, setActiveIndex] = useState<number>(0); // Explicitly type useState

  return (
    <section className="bg-black pt-5 pb-20">
      <div className="container mx-auto px-1">
        <div className="grid grid-rows-1 md:grid-cols-2 gap-1">
          <div className="md:row-span-2">
            <div className="grid grid-rows-1 sm:grid-rows-2 lg:grid-rows-3 gap-2">
              {features.map((feature, index) => (
                <div
                  key={index}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(index)}
                  className={`bg-black rounded-[20px] p-4 flex items-center gap-4 max-w-[500px] transition-all duration-300 ${
                    activeIndex === index
                      ? "shadow-[0_0_20px_rgba(255,255,255,0.4)] scale-105"
                      : ""
                  }`}
                >
                  <div className="relative w-16 h-16 mb-4">
                    <Image
                      src={feature.icon}
                      alt={`${feature.title} icon`}
                      fill
                      className="object-contain"
                    />
                  </div>
                  <div className="flex flex-col">
                    <div className="mt-[1rem] mb-[1rem] text-lg font-bold text-white">
                      <h4>{feature.title}</h4>
                    </div>
                    <p className="text-base text-gray-400 font-normal m-0">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
          {/* Placeholder for animation */}
          <div className="hidden md:flex items-center justify-center">
            <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Animation Placeholder</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};