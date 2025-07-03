"use client";
import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface FAQ {
  question: string;
  answer: string;
}

const faqs: FAQ[] = [
  {
    question: "What is Alphintra and how does it work?",
    answer: "Alphintra is a no-code trading automation platform that allows you to create, test, and deploy sophisticated trading strategies without writing any code. Simply drag and drop components to build your strategy, backtest it on historical data, and deploy it for automated trading."
  },
  {
    question: "Do I need programming knowledge to use Alphintra?",
    answer: "No! Alphintra is designed for traders of all technical backgrounds. Our visual, drag-and-drop interface makes it easy to create complex trading strategies without any coding knowledge. However, if you do have programming skills, you can also customize and extend your strategies."
  },
  {
    question: "What markets and assets can I trade?",
    answer: "Alphintra supports major cryptocurrency exchanges and traditional markets. You can trade cryptocurrencies, forex, stocks, and other financial instruments. Our platform integrates with leading exchanges to provide real-time data and execution capabilities."
  },
  {
    question: "How much does Alphintra cost?",
    answer: "We offer multiple pricing tiers to suit different needs. Start with our free tier that includes basic features and limited strategies. Paid plans offer advanced features, unlimited strategies, real-time data, and priority support. Check our pricing page for detailed information."
  },
  {
    question: "Is my money and data secure?",
    answer: "Absolutely. We use bank-level security with end-to-end encryption, multi-factor authentication, and secure API connections. Your funds remain in your own exchange accounts - we never have direct access to your money. All data is encrypted and stored securely."
  },
  {
    question: "Can I test my strategies before going live?",
    answer: "Yes! Alphintra includes comprehensive backtesting tools that let you test your strategies on historical data. You can also use paper trading to test strategies in real-time without risking actual money. Only deploy live when you're confident in your strategy's performance."
  }
];

export const FAQ = () => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id="faq" className="bg-black py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Frequently Asked Questions</h2>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Got questions? We've got answers. Here are the most common questions about Alphintra.
          </p>
        </div>
        
        <div className="max-w-3xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white/5 backdrop-blur-sm rounded-lg border border-white/10 overflow-hidden"
            >
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full px-6 py-4 text-left flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <h3 className="text-lg font-semibold text-white pr-4">
                  {faq.question}
                </h3>
                {openIndex === index ? (
                  <ChevronUp className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                )}
              </button>
              
              {openIndex === index && (
                <div className="px-6 pb-4">
                  <p className="text-gray-300 leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};