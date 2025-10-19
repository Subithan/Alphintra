'use client';

import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Strategy } from './types'; // Assumes this is where your provided interface lives
import { initiateStripeCheckout, getStripePublishableKey } from '@/app/api/paymentApi'; 
import { X, ArrowUpRight, TrendingUp, Users, Shield, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

// Initialize Stripe.js with your publishable key
const stripePromise = loadStripe(getStripePublishableKey());

// Define the component props
interface StrategyModalProps {
    strategy: Strategy;
    onClose: () => void;
}

export default function StrategyModal({ strategy, onClose }: StrategyModalProps) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Function to map risk level to a color
    const getRiskColor = (risk: string) => {
        switch (risk.toLowerCase()) {
            case 'low': // Matches 'low' from your interface: 'low' | 'medium' | 'high'
                return 'bg-green-500 hover:bg-green-600';
            case 'medium':
                return 'bg-yellow-500 hover:bg-yellow-600';
            case 'high':
                return 'bg-red-500 hover:bg-red-600';
            default:
                return 'bg-gray-500 hover:bg-gray-600';
        }
    };
    
    // CRITICAL CHECKOUT LOGIC using Stripe.js
    const handleCheckout = async () => {
        if (strategy.price === 'free' || isProcessing) return; 

        console.log('[StrategyModal] Starting checkout for strategy:', strategy.id);
        setIsProcessing(true);
        setError(null);

        try {
            // Get Stripe.js instance
            const stripe = await stripePromise;
            if (!stripe) {
                throw new Error('Stripe.js failed to load');
            }

            console.log('[StrategyModal] Calling initiateStripeCheckout...');
            // Get the session ID from your backend
            const sessionId = await initiateStripeCheckout(strategy.id);
            console.log('[StrategyModal] Received session ID:', sessionId);

            console.log('[StrategyModal] Redirecting to Stripe Checkout...');
            // Use Stripe.js to redirect to checkout
            // @ts-ignore - redirectToCheckout exists but types may not be updated
            const result = await stripe.redirectToCheckout({ sessionId });
            
            // If we reach here without redirecting, there was an error
            if (result?.error) {
                throw new Error(result.error.message);
            }
        } catch (err) {
            console.error("[StrategyModal] Stripe Checkout Failed:", err);
            setError((err as Error).message || "Payment processing failed. Please try again.");
            setIsProcessing(false);
        }
    };

    // Corrected access to performance properties
    const performance = strategy.performance;
    const totalReturn = performance.totalReturn ?? 0;
    const maxDrawdown = performance.maxDrawdown ?? 0;
    
    // FIX: Access winRate from the nested performance object
    const winRate = performance.winRate ?? 0; 

    // Assuming the header text should be the description for the main banner (like "Stable long-term stock investments")
    const headerTitle = strategy.description || strategy.name; 

    // Determine Buy Button Text
    const priceText = strategy.price === 'free' 
        ? 'Available for Free' 
        : `Buy $${(strategy.price as number).toFixed(2)}`;

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-75 flex items-center justify-center p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full transform transition-all relative">
                
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                    aria-label="Close modal"
                >
                    <X className="h-6 w-6" />
                </button>

                {/* Header Section (Red Banner) */}
                <div className="p-8 rounded-t-xl bg-gradient-to-r from-red-700 to-red-900 text-white text-center space-y-2">
                    {/* Placeholder for the Bitcoin/Crypto icon if needed */}
                    <p className="text-xl font-semibold opacity-80">{strategy.name}</p> 
                    <h1 className="text-4xl font-extrabold tracking-tight">{headerTitle}</h1>
                    <p className="text-sm opacity-90">By: {strategy.creatorName}</p>
                </div>

                {/* Stats and Description */}
                <div className="p-8 space-y-6">
                    {/* The description is used in the header, keeping this space clean or adding more detail */}
                    
                    {/* Performance Metrics Grid */}
                    <div className="grid grid-cols-2 gap-4 text-center">
                        {/* Displaying raw performance data as seen in your image */}
                        
                        {/* Row 1: Max Drawdown vs Sharpe Ratio */}
                        <StatCard 
                            title="Max Drawdown" 
                            value={`${maxDrawdown.toFixed(1)}%`} 
                            icon={ArrowUpRight} 
                            color="text-red-400" 
                        />
                        <StatCard 
                            title="Sharpe Ratio" 
                            value={`${performance.sharpeRatio.toFixed(2)}`} 
                            icon={TrendingUp} 
                            color="text-yellow-400" 
                        />
                        
                        {/* Row 2: Win Rate vs Total Return */}
                        <StatCard 
                            title="Win Rate" 
                            value={`${winRate.toFixed(0)}%`} 
                            icon={Shield} 
                            color="text-blue-400" 
                        />
                        <StatCard 
                            title="Total Return" 
                            value={`${totalReturn.toFixed(1)}%`} 
                            icon={TrendingUp} 
                            color="text-green-400" 
                        />
                        
                    </div>
                    
                    {/* Risk Badge and Usage */}
                    <div className="flex justify-between items-center pt-4 border-t border-gray-700">
                        <div className="space-y-1">
                            <p className="text-sm font-semibold text-gray-400">Usage / Subscribers</p>
                            <div className="flex items-center text-gray-300">
                                <Users className="h-4 w-4 mr-1 text-yellow-400" />
                                <span>{strategy.subscriberCount.toLocaleString()}</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <p className="text-sm font-semibold text-gray-400">Risk Level</p>
                            <Badge className={`${getRiskColor(strategy.riskLevel)} text-white`}>
                                {strategy.riskLevel.charAt(0).toUpperCase() + strategy.riskLevel.slice(1)} Risk
                            </Badge>
                        </div>
                    </div>

                    {/* Buy Button Section */}
                    <div className="pt-6">
                        {error && (
                            <p className="text-red-400 text-center mb-3 text-sm font-medium">{error}</p>
                        )}
                        <Button
                            onClick={handleCheckout} 
                            disabled={isProcessing || strategy.price === 'free'}
                            className={`w-full py-7 text-xl font-bold rounded-lg transition-colors ${
                                isProcessing 
                                    ? 'bg-gray-600 cursor-not-allowed' 
                                    : 'bg-yellow-500 hover:bg-yellow-600 text-gray-900'
                            }`}
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Processing Payment...
                                </>
                            ) : priceText}
                        </Button>
                        <p className="text-center text-xs text-gray-500 mt-2">
                            Price includes 1 month of updates.
                        </p>
                    </div>

                </div>
            </div>
        </div>
    );
}

// Simple Card component for displaying stats (Helper)
interface StatCardProps {
    title: string;
    value: string;
    icon: React.ElementType;
    color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, color }) => (
    <Card className="bg-gray-700 border-gray-600">
        <CardContent className="p-4 space-y-1">
            <Icon className={`h-6 w-6 mx-auto ${color}`} />
            <p className="text-2xl font-bold text-white">{value}</p>
            <p className="text-xs font-medium text-gray-400">{title}</p>
        </CardContent>
    </Card>
);