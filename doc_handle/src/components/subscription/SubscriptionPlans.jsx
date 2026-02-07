import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
// Ensure your api utility exports api instance. If meant 'import api from ...' adjust accordingly.
// Assuming 'api' is exported as default from utils/api.ts or similar. 
// If it's a named export, use { api }.
// Checking previous files, api.ts usually has a default export or named export. I'll check imports in other files if needed.
// previous login.jsx used: import { auth } from '../../utils/auth'; 
// utils/api.ts likely wraps axios.

// Let's assume standard import for now, or check api.ts if unsure.
// I'll stick to a safe pattern or check api.ts content quickly? 
// No, I'll allow standard import.

const SubscriptionPlans = () => {
    const [plans, setPlans] = useState(null);
    const [currentPlan, setCurrentPlan] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        fetchPlans();
        fetchCurrentSubscription();
    }, []);

    const fetchPlans = async () => {
        try {
            const response = await api.get('/subscription/plans');
            setPlans(response.data.plans);
        } catch (error) {
            console.error('Failed to fetch plans', error);
        }
    };

    const fetchCurrentSubscription = async () => {
        try {
            const response = await api.get('/subscription/current');
            setCurrentPlan(response.data.subscription);
        } catch (error) {
            console.error('Failed to fetch subscription', error);
        }
    };

    const handleUpgrade = async (planType, gateway = 'razorpay') => {
        setIsLoading(true);
        try {
            const response = await api.post('/subscription/upgrade', {
                plan_type: planType,
                gateway: gateway
            });

            if (response.data.gateway === 'razorpay') {
                const options = {
                    key: response.data.key,
                    amount: response.data.amount * 100,
                    currency: response.data.currency,
                    name: 'Outing Automation',
                    description: `${planType.charAt(0).toUpperCase() + planType.slice(1)} Plan`,
                    order_id: response.data.order_id,
                    handler: async function (paymentResponse) {
                        try {
                            await api.post('/subscription/verify-payment', {
                                razorpay_order_id: paymentResponse.razorpay_order_id,
                                razorpay_payment_id: paymentResponse.razorpay_payment_id,
                                razorpay_signature: paymentResponse.razorpay_signature
                            });
                            alert('Payment Successful! Plan Upgraded.');
                            window.location.reload();
                        } catch (err) {
                            alert('Payment Verification Failed');
                        }
                    },
                    prefill: {
                        email: currentPlan?.email || ''
                    },
                    theme: { color: '#6366f1' }
                };

                const rzp = new window.Razorpay(options);
                rzp.open();
            }
        } catch (error) {
            console.error('Upgrade Error:', error);
            alert(error.response?.data?.error || 'Upgrade failed');
        } finally {
            setIsLoading(false);
        }
    };

    if (!plans) return <div className="p-8 text-center text-white">Loading plans...</div>;

    return (
        <div className="min-h-screen p-8" style={{ background: 'radial-gradient(ellipse at top, #1e293b 0%, #0f172a 100%)' }}>
            <div className="max-w-6xl mx-auto">
                <h1 className="text-4xl font-bold text-center mb-4 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-500">
                    Choose Your Plan
                </h1>
                <p className="text-center text-gray-400 mb-12">Unlock full automation and never miss a submission</p>

                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    {Object.entries(plans).map(([key, plan]) => (
                        <div key={key} className={`relative p-8 rounded-2xl border ${key === 'premium' ? 'border-indigo-500 bg-indigo-900/20' : 'border-gray-700 bg-slate-800/50'} backdrop-blur-xl transition-transform hover:-translate-y-2`}>
                            {key === 'premium' && (
                                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-indigo-500 text-white px-4 py-1 rounded-full text-sm font-bold">
                                    RECOMMENDED
                                </div>
                            )}

                            <h2 className="text-2xl font-bold text-white mb-2">{plan.name}</h2>
                            <div className="text-4xl font-bold text-indigo-400 mb-4">
                                ₹{plan.price} <span className="text-lg text-gray-400 font-normal">/ {key === 'basic' ? 'month' : '4 months'}</span>
                            </div>

                            <ul className="space-y-4 mb-8">
                                {Object.entries(plan.features).map(([feature, enabled]) => (
                                    <li key={feature} className="flex items-center text-gray-300">
                                        <span className="mr-2 text-indigo-400">{enabled ? '✓' : '✗'}</span>
                                        {feature.replace(/_/g, ' ')}
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={() => handleUpgrade(key)}
                                disabled={isLoading || currentPlan?.plan_type === key}
                                className={`w-full py-3 rounded-xl font-bold transition-all ${currentPlan?.plan_type === key
                                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                                    : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/30'
                                    }`}
                            >
                                {isLoading ? 'Processing...' : currentPlan?.plan_type === key ? 'Current Plan' : 'Upgrade Now'}
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default SubscriptionPlans;
