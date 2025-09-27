import { Zap } from "lucide-react";
import React from "react";
import Loader from "@/components/ui/Loader";
import { useBotProgress } from "@/components/hooks/useBotProgress";

export const Hero = () => {
  const { progress, status } = useBotProgress(7000);
  return (
    <section className="text-white bg-transparent pt-24 pb-16 min-h-screen flex items-center glass-gradient">
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <defs>
          <linearGradient id="text-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style={{ stopColor: "#F87AFF" }} />
            <stop offset="25%" style={{ stopColor: "#FB93D0" }} />
            <stop offset="50%" style={{ stopColor: "#FFDD00" }} />
            <stop offset="75%" style={{ stopColor: "#C3F0B2" }} />
            <stop offset="100%" style={{ stopColor: "#2FD8FE" }} />
          </linearGradient>
        </defs>
      </svg>
      <div className="container mx-auto px-4">
        <div className="relative isolate">
          <div className="absolute inset-0 -z-20">
            {/* Gradient background effects can be added here */}
          </div>
          <div className="relative z-10 flex flex-col lg:flex-row items-center justify-center gap-12">
            {/* Text Column: badge, h1, p, button */}
            <div className="w-full lg:w-1/2 text-left">
              <div className="flex items-center justify-start">
                <p className="inline-flex items-center gap-2 border py-1 px-2 rounded-lg border-white/30 bg-white/10 backdrop-blur-md">
                  <Zap
                    size={20}
                    className="text-transparent"
                    style={{
                      stroke: "url(#text-gradient)",
                      fill: "none",
                      strokeWidth: 1,
                    }}
                    aria-hidden="true"
                  />
                  <span className="bg-[linear-gradient(to_right,#F87AFF,#FB93D0,#FFDD00,#C3F0B2,#2FD8FE)] text-transparent bg-clip-text [-webkit-background-clip:text]">
                    No-Code Trading Automation
                  </span>
                </p>
              </div>
              <h1 className="text-5xl lg:text-6xl font-bold leading-tight text-gray-100 mt-5">
                Build Trading Bots
                <br />
                <span>Without Code</span>
              </h1>
              <p className="text-lg mt-4 max-w-2xl text-gray-100">
                Create sophisticated trading strategies using our intuitive drag-and-drop interface. Automate your trades with
                AI-powered bots - 24/7.
              </p>
              <div className="mt-6">
                <button
                  type="button"
                  className="inline-block bg-yellow-400 text-[#312e81] px-6 py-3 rounded-lg font-semibold text-lg hover:scale-105 transition-colors"
                  aria-label="Get started with trading automation"
                >
                  Get Started
                </button>
              </div>
            </div>
            {/* Visual Column: Alphintra Robot + enhanced loader */}
            <div className="w-full lg:w-1/2 flex flex-col items-center">
              <div className="w-full max-w-[800px] h-[450px] rounded-2xl overflow-hidden border border-white/10 bg-black/30 backdrop-blur-md relative">
                {/* Ambient gradients */}
                <div className="absolute inset-0 bg-[radial-gradient(1200px_600px_at_0%_0%,rgba(255,221,0,0.18),transparent_60%),radial-gradient(1000px_600px_at_100%_0%,rgba(168,85,247,0.16),transparent_60%),radial-gradient(1000px_800px_at_50%_100%,rgba(34,197,94,0.14),transparent_60%)]" />
                <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.06)_0%,rgba(255,255,255,0.02)_100%)]" />

                {/* Robot */}
                <div className="robot absolute inset-0">
                  <div className="robot-head mx-auto mt-10">
                    <span className="robot-eye left" />
                    <span className="robot-eye right" />
                    <span className="robot-scan" />
                  </div>
                  <div className="robot-body mx-auto">
                    <span className="robot-chest-led" />
                  </div>
                </div>

                {/* Enhanced loader - bound to bot progress */}
                <div className="absolute bottom-3 w-full px-4">
                  <div className="bot-loader backdrop-blur-md flex items-center justify-between gap-3 px-4 py-3 rounded-2xl w-[360px] max-w-full mx-auto">
                    <div className="flex items-center gap-2 text-sm text-gray-100 font-medium">
                      <Loader className="text-gray-100 w-4 h-4" />
                      {status === "online" ? "Bot Online" : status === "syncing" ? "Syncing" : "Starting Bot"}
                    </div>
                    <span className="text-[10px] text-gray-300">{progress}%</span>
                  </div>
                  <div className="bot-progress w-[360px] max-w-full mx-auto">
                    <div className="bot-progress-bar" style={{ width: `${Math.max(10, progress)}%` }} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};