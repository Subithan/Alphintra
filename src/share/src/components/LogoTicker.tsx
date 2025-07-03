"use client";

import bitcoin from "../app/assets/images/Bitcoin.png";
import ethereum from "../app/assets/images/Ethereum.png";
import TRON from "../app/assets/images/TRON.png";
import XRP from "../app/assets/images/XRP.png";
import DOGE from "../app/assets/images/DOGE.png";
import SHIB from "../app/assets/images/SHIB.png";
import USDT from "../app/assets/images/USDT.png";
import ADA from "../app/assets/images/ADA.png";
import Image from "next/image";
import { motion } from "framer-motion";
import React from 'react'; // Import React for JSX in TypeScript
import { StaticImageData } from 'next/image'; // Import StaticImageData type

interface ImageItem {
  src: StaticImageData;
  alt: string;
}

const images: ImageItem[] = [
  { src: bitcoin, alt: "Bitcoin" },
  { src: ethereum, alt: "Ethereum" },
  { src: TRON, alt: "TRON" },
  { src: XRP, alt: "XRP" },
  { src: DOGE, alt: "Dogecoin" },
  { src: SHIB, alt: "SHIB" },
  { src: USDT, alt: "USDT" },
  { src: ADA, alt: "ADA" },
];

export const LogoTicker = () => {
  return (
    <div className="bg-black text-black py-[72px] py-24 mt-0">
      <div className="container">
        <div className="flex overflow-hidden mt-9 before:content-[''] before:z-10 after:content-[''] before:absolute after:absolute before:h-full after:h-full before:w-5 after:w-5 relative before:left-0 after:right-0 before:top-0 after:top-0 before:bg-[linear-gradient(to_right,#000,rgb(0,0,0,0))] after:bg-[linear-gradient(to_left,#000,rgb(0,0,0,0))]">
          <motion.div
            transition={{
              duration: 20,
              ease: "linear",
              repeat: Infinity,
            }}
            initial={{ translateX: 0 }}
            animate={{ translateX: "-50%" }}
            className="flex gap-16 flex-none pr-16"
          >
            {images.map(({ src, alt }, index) => (
              <Image
                key={index}
                src={src}
                alt={alt}
                className="flex-none h-8 w-auto"
                width={100} // Specify width for next/image
                height={32} // Specify height for next/image
              />
            ))}
            {images.map(({ src, alt }, index) => (
              <Image
                key={index}
                src={src}
                alt={alt}
                className="flex-none h-8 w-auto"
                width={100} // Specify width for next/image
                height={32} // Specify height for next/image
              />
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  );
};