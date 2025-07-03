"use client"
import { Plus } from "lucide-react";
import React, { useState, useRef, useEffect, FC } from "react"; // Import FC for functional component
import clsx from "clsx";

interface FAQItem {
  question: string;
  answer: string;
}

const faqs: FAQItem[] = [
  {
    question: "How does the no-code trading bot builder work?",
    answer: "Build trading strategies using a drag-and-drop interface. No coding needed.",
  },
  {
    question: "Is my money and data safe with Alpintra?",
    answer: "Yes. We use bank-level encryption and never store withdrawal-enabled API keys.",
  },
  {
    question: "What exchanges are supported?",
    answer: "Supports major exchanges like Binance, Coinbase Pro, Kraken, Bybit, and more.",
  },
  {
    question: "Do I need any programming knowledge?",
    answer: "No coding required. Anyone can build strategies using simple visual tools.",
  },
  {
    question: "Can I test my strategies before using real money?",
    answer: "Yes. Use backtesting or paper trading to test without risking real money.",
  },
  {
    question: "What's the pricing structure?",
    answer: "Free tier available. Paid plans start at $29/month with more features.",
  },
  {
    question: "What kind of support do you provide?",
    answer: "We offer 24/7 chat, docs, video tutorials, and weekly webinars.",
  },
  {
    question: "How do I get started?",
    answer: "Sign up, connect your exchange, and choose a strategy to start.",
  },
];

interface AccordionItemProps {
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
}

const AccordionItem: FC<AccordionItemProps> = ({ question, answer, isOpen, onClick }) => {
  const contentRef = useRef<HTMLDivElement>(null); // Specify type for useRef
  const [height, setHeight] = useState<string>("0px"); // Explicitly type useState

  useEffect(() => {
    if (isOpen) {
      setHeight(`${contentRef.current?.scrollHeight}px`); // Use optional chaining
    } else {
      setHeight("0px");
    }
  }, [isOpen]);

  return (
    <div
      className="py-7 border-b border-white/30 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <span className="flex-1 text-lg font-bold">{question}</span>
        <Plus
          className={clsx("transition-transform duration-300", {
            "rotate-45": isOpen,
          })}
        />
      </div>
      <div
        ref={contentRef}
        style={{
          maxHeight: height,
          transition: "max-height 0.3s ease, opacity 0.3s ease",
          opacity: isOpen ? 1 : 0,
          overflow: "hidden",
        }}
        className="mt-3 max-w-[648px] text-gray-300 text-base"
      >
        {answer}
      </div>
    </div>
  );
};

export const FAQs = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null); // Explicitly type useState

  const handleClick = (index: number) => { // Explicitly type index
    setOpenIndex((prev) => (prev === index ? null : index));
  };

  return (
    <div className="bg-black text-white bg-gradient-to-b from-[#312e81] to-black py-[72px]">
      <div className="container px-4 max-w-3xl mx-auto">
        <h2 className="text-center text-5xl font-bold tracking-tighter">
          Frequently Asked Questions
        </h2>
        <div className="mt-12">
          {faqs.map(({ question, answer }, index) => (
            <AccordionItem
              key={question}
              question={question}
              answer={answer}
              isOpen={openIndex === index}
              onClick={() => handleClick(index)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};