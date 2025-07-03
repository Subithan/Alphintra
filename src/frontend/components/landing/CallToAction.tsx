import React from "react";
import Link from "next/link";
import { ArrowRight, Zap } from "lucide-react";

export const CallToAction = () => {
  return (
    <section id="updates" className="bg-gradient-to-r from-yellow-500 to-yellow-600 py-20">
      <div className="container mx-auto px-4">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 bg-black/20 px-4 py-2 rounded-full mb-6">
            <Zap className="w-5 h-5 text-black" />
            <span className="text-black font-medium">Start Trading Today</span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold text-black mb-6">
            Ready to Transform Your Trading?
          </h2>
          
          <p className="text-xl text-black/80 mb-8 leading-relaxed">
            Join thousands of successful traders using Alphintra to maximize their trading potential 
            with AI-powered strategies. No coding required, just results.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/auth"
              className="inline-flex items-center gap-2 bg-black text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-black/90 transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-105"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5" />
            </Link>
            
            <Link
              href="#features"
              className="inline-flex items-center gap-2 border-2 border-black text-black px-8 py-4 rounded-lg font-semibold text-lg hover:bg-black hover:text-white transition-all duration-200"
            >
              Learn More
            </Link>
          </div>
          
          <div className="mt-8 flex items-center justify-center gap-8 text-black/60">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-black/40 rounded-full"></div>
              <span className="text-sm">No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-black/40 rounded-full"></div>
              <span className="text-sm">Free forever plan</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-black/40 rounded-full"></div>
              <span className="text-sm">Cancel anytime</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};