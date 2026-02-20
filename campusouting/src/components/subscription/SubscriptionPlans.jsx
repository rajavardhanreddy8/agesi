import React, { useState, useEffect } from 'react';
import api from '../../utils/api';

const SubscriptionPlans = () => {
    const [plans, setPlans] = useState(null);
    const [currentPlan, setCurrentPlan] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        fetchPlans();
        fetchCurrentSubscription();
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        document.body.appendChild(script);
        return () => {
            document.body.removeChild(script);
        };
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
                            alert('Payment Successful! Plan Upgraded to ' + planType);
                            window.location.href = '/dashboard';
                        } catch (err) {
                            console.error(err);
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

    if (!plans) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#070d1a]">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin shadow-[0_0_15px_rgba(99,102,241,0.5)]"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen relative overflow-hidden bg-[#070d1a] font-sans text-slate-200 py-16 px-6 sm:px-10 flex flex-col items-center">
            {/* Animated Glow Background Effects */}
            <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-indigo-600/20 blur-[120px] mix-blend-screen pointer-events-none animate-pulse" style={{ animationDuration: '6s' }}></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-fuchsia-600/10 blur-[150px] mix-blend-screen pointer-events-none animate-pulse" style={{ animationDuration: '8s', animationDelay: '2s' }}></div>

            <div className="relative z-10 max-w-5xl w-full text-center mb-16 mt-8">
                <div className="inline-block mb-4 px-4 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 backdrop-blur-md">
                    <span className="bg-gradient-to-r from-indigo-400 to-fuchsia-400 text-transparent bg-clip-text font-bold text-sm tracking-widest uppercase">
                        Campus Automation
                    </span>
                </div>
                <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6 text-white leading-tight">
                    Elevate Your <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-fuchsia-400 text-transparent bg-clip-text">Experience</span>
                </h1>
                <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto font-light leading-relaxed">
                    Unlock limitless potential with complete outing automation. Say goodbye to missed forms and hello to instant approvals.
                </p>
            </div>

            <div className="relative z-10 w-full max-w-md mx-auto perspective-1000">
                {Object.entries(plans).map(([key, plan]) => {
                    const isCurrentPlan = currentPlan?.plan_type === key || (currentPlan && currentPlan?.plan_type !== 'free' && currentPlan?.plan_type !== 'plan');

                    return (
                        <div
                            key={key}
                            className="group relative flex flex-col p-px rounded-[2rem] overflow-hidden transition-all duration-500 hover:scale-[1.02] hover:-translate-y-2 hover:shadow-[0_20px_60px_-15px_rgba(99,102,241,0.4)]"
                        >
                            {/* Animated Gradient Border */}
                            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500 via-purple-500 to-fuchsia-500 opacity-60 group-hover:opacity-100 transition-opacity duration-500 rounded-[2rem]"></div>

                            {/* Card Content Backing */}
                            <div className="relative flex-1 flex flex-col bg-[#0b1329]/95 backdrop-blur-2xl rounded-[calc(2rem-1px)] p-10 sm:p-12 w-full h-full overflow-hidden">

                                {/* Inner glow */}
                                <div className="absolute top-0 right-0 -mt-16 -mr-16 w-32 h-32 bg-gradient-to-br from-indigo-500 to-fuchsia-500 rounded-full blur-3xl opacity-30 group-hover:opacity-60 transition-opacity duration-500"></div>

                                <div className="text-center mb-10 relative">
                                    <h2 className="text-3xl font-bold text-white mb-4 tracking-tight">{plan.name}</h2>
                                    <div className="flex justify-center items-baseline gap-2">
                                        <span className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-300 to-white">
                                            ₹{plan.price}
                                        </span>
                                        <span className="text-lg text-slate-400 font-medium tracking-wide">/ mo</span>
                                    </div>
                                </div>

                                <div className="flex-1">
                                    <ul className="space-y-5 mb-10">
                                        {Object.entries(plan.features).map(([feature, enabled]) => (
                                            <li key={feature} className="flex items-start">
                                                <div className="flex-shrink-0 mt-1">
                                                    {enabled ? (
                                                        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-400 ring-1 ring-indigo-500/50 shadow-[0_0_10px_rgba(99,102,241,0.3)]">
                                                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                                                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        </div>
                                                    ) : (
                                                        <div className="flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 text-slate-500 ring-1 ring-slate-700">
                                                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                                                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                                                            </svg>
                                                        </div>
                                                    )}
                                                </div>
                                                <span className={`ml-4 text-base ${enabled ? 'text-slate-200' : 'text-slate-500'} font-medium`}>
                                                    {feature.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                <button
                                    onClick={() => handleUpgrade(key)}
                                    disabled={isLoading || isCurrentPlan}
                                    className={`relative w-full py-4 rounded-xl font-bold tracking-wide transition-all duration-300 overflow-hidden outline-none ring-offset-2 ring-offset-[#070d1a] focus:ring-2 focus:ring-indigo-500 ${isCurrentPlan
                                        ? 'bg-slate-800/80 text-slate-400 cursor-not-allowed border border-slate-700'
                                        : 'text-white transform active:scale-[0.98] shadow-[0_0_20px_rgba(99,102,241,0.4)] hover:shadow-[0_0_30px_rgba(192,132,252,0.6)]'
                                        }`}
                                >
                                    {!isCurrentPlan && (
                                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-fuchsia-500 hover:from-indigo-400 hover:via-purple-400 hover:to-fuchsia-400 transition-colors z-0"></div>
                                    )}
                                    <span className="relative z-10 flex items-center justify-center gap-2">
                                        {isLoading ? (
                                            <>
                                                <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                                Processing Securely...
                                            </>
                                        ) : isCurrentPlan ? '✓ Current Plan Active' : 'Start Automating Now'}
                                    </span>
                                </button>

                                <p className="text-center text-xs text-slate-500 mt-6 font-medium flex items-center justify-center gap-1.5">
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                                    Secured by Razorpay Encryption
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default SubscriptionPlans;
