"use client";

import { Settings } from "lucide-react";
import React from "react"; // Import React for JSX in TypeScript

interface Strategy {
  name: string;
  description: string;
  performance: string;
  risk: string;
  active: boolean;
}

// Sample data (replace with actual data or props)
const strategies: Strategy[] = [
  {
    name: "Mean Reversion",
    description: "Buys assets that have dropped in price expecting a rebound.",
    performance: "+12.5%",
    risk: "Low",
    active: true,
  },
  {
    name: "Momentum Trading",
    description: "Follows trends to capitalize on asset movements.",
    performance: "+18.2%",
    risk: "Medium",
    active: false,
  },
  {
    name: "Breakout Strategy",
    description: "Trades based on price breaking resistance or support levels.",
    performance: "+22.3%",
    risk: "High",
    active: true,
  },
];

export const Strategies = () => {
  return (
    <section className=" text-white bg-gradient-to-b to-[#312e81] from-black py-[72px]">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Popular Strategy Templates</h2>
          <p className="text-gray-300 max-w-2xl mx-auto text-xl">
            Start with proven strategies or customize them to fit your trading style.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy, index) => (
            <div
              key={index}
              className="bg-black rounded-[20px] shadow-md p-6 hover:shadow-xl hover:scale-105 transition-all duration-300"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold">{strategy.name}</h3>
                <span
                  className={`inline-block px-2 py-1 text-xs rounded ${
                    strategy.active ? "bg-blue-400 text-[#312e81]" : "bg-gray-200 text-gray-600"
                  }`}
                >
                  {strategy.active ? "Active" : "Inactive"}
                </span>
              </div>
              <p className="text-gray-600 mb-4">{strategy.description}</p>

              <div className="flex justify-between items-center mb-4">
                <div>
                  <p className="text-sm text-gray-500">Performance</p>
                  <p className="text-lg font-semibold text-green-600">{strategy.performance}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Risk Level</p>
                  <p className="text-lg font-semibold">{strategy.risk}</p>
                </div>
              </div>

              <button className="w-full border border-gray-300 rounded px-4 py-2 flex items-center justify-center hover:bg-gray-100 transition">
                <Settings className="h-4 w-4 mr-2" />
                Customize Strategy
              </button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};