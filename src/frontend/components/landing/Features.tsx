"use client";
import React, { useState } from "react";
import { BarChart3, TrendingUp, Activity, Shield } from "lucide-react";

interface Feature {
  icon: React.ComponentType<any>;
  title: string;
  description: string;
}

const features: Feature[] = [
  {
    icon: TrendingUp,
    title: "Automatic Trading",
    description:
      "Crypto trading is 24/7. So is your bot. Give yourself an edge, and while everyone else sleeps, you'll never miss a beat.",
  },
  {
    icon: BarChart3,
    title: "Custom Strategies",
    description:
      "Create and deploy your own trading strategies tailored to your risk profile and market goals.",
  },
  {
    icon: Activity,
    title: "Real-Time Analytics",
    description:
      "Gain insights with real-time market data and performance tracking to optimize your trades.",
  },
  {
    icon: Shield,
    title: "Backtesting",
    description:
      "Test your strategies on historical data before deploying real capital.",
  },
];

export const Features = () => {
  const [activeIndex, setActiveIndex] = useState<number>(0);

  return (
    <section id="features" className="bg-gray-900 py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Powerful Features</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Everything you need to build, test, and deploy successful trading strategies
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <div
                  key={index}
                  onMouseEnter={() => setActiveIndex(index)}
                  onMouseLeave={() => setActiveIndex(index)}
                  className={`bg-gray-800 rounded-[20px] p-6 flex items-start gap-4 max-w-[500px] transition-all duration-300 border border-white/10 ${
                    activeIndex === index
                      ? "shadow-[0_0_20px_rgba(255,221,0,0.4)] scale-105 border-yellow-400/50"
                      : "hover:border-white/20"
                  }`}
                >
                  <div className="w-12 h-12 bg-yellow-400 rounded-lg flex items-center justify-center flex-shrink-0">
                    <IconComponent className="w-6 h-6 text-black" />
                  </div>
                  <div className="flex flex-col">
                    <h4 className="text-lg font-bold text-white mb-2">
                      {feature.title}
                    </h4>
                    <p className="text-base text-gray-400 font-normal leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Visual representation */}
          <div className="hidden md:flex items-center justify-center">
            <div className="w-full h-96 bg-gradient-to-br from-yellow-400/10 to-purple-500/10 rounded-lg border border-white/10 flex items-center justify-center relative overflow-hidden">
              <div className="text-center z-10">
                <div className="w-24 h-24 mx-auto mb-6 bg-yellow-400 rounded-full flex items-center justify-center">
                  <BarChart3 className="w-12 h-12 text-black" />
                </div>
                <h3 className="text-white text-xl font-semibold mb-2">No-Code Interface</h3>
                <p className="text-gray-400">Drag, drop, and deploy</p>
              </div>
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,221,0,0.1)_0%,transparent_70%)]"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};