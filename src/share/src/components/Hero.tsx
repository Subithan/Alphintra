import { Zap } from "lucide-react";
import robotImg from "../app/assets/images/robot.jpg";
import Image from "next/image";
import Loader from "../app/assets/svg/loader.js"; // This might need to be converted to .tsx as well
import React from "react"; // Import React for JSX in TypeScript

export const Hero = () => {
  return (
    <section className="text-white bg-black">
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
      <div className="container">
        <div className="container py-8 relative isolate">
          <div className="absolute inset-0 -z-20">
            {/* Gradient circle */}
            {/* <div className="absolute inset-0 bg-[radial-gradient(circle_farthest-corner,#312e81_25%,#000_55%,transparent)] rounded-full [mask-image:radial-gradient(circle_farthest-side,black,transparent)]" /> */}
            {/* <div className="absolute inset-0 flex items-center justify-center -z-10 relative">
              <Orbit className="w-[600px] h-[600px]" />
              <Orbit
                className="w-[350px] h-[350px] absolute"
                style={{ top: '25%', left: '50%', transform: 'translate(-50%, -50%)' }}
              />
            </div> */}
          </div>
          <div className="relative z-10 mt-16 flex flex-col lg:flex-row items-center justify-center gap-8">
            {/* Text Column: badge, h1, p, button */}
            <div className="w-full lg:w-1/2 text-left">
              <div className="flex items-center justify-start">
                <p className="inline-flex items-center gap-2 border py-1 px-2 rounded-lg border-white/30 bg-white/10">
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
            {/* Image Column */}
            <div className="w-full lg:w-1/2 flex flex-col items-center">
              <div className="w-full max-w-[800px] h-[450px] rounded-2xl border-2 overflow-hidden border-transparent [background:linear-gradient(#0a0a0a,#0a0a0a)_padding-box,conic-gradient(from_45deg,#a78bfa,#e879f9,#fcd34d,#5eead4,#a78bfa)_border-box] relative">
                <Image
                  src={robotImg}
                  alt="Robot trading bot interface"
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-2 w-full px-4">
                  <div className="bg-gray-950/80 flex items-center justify-center px-4 py-2 rounded-2xl w-[320px] max-w-full mx-auto">
                    <div className="font-semibold text-xs text-gray-100 flex items-center gap-2">
                      <Loader className="text-gray-100" /> {/* Loader might need type definition */}
                      Starting Bot
                    </div>
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