import React, { useState, useEffect } from 'react';
import api from '../../utils/api';

const SubscriptionPlans = () => {
    const [plans, setPlans] = useState(null);
    const [currentPlan, setCurrentPlan] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [hover, setHover] = useState(false);

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

            if (response.data.gateway === 'free') {
                alert('Plan Changed Successfully!');
                fetchCurrentSubscription();
                window.location.href = '/dashboard';
                return;
            }

            if (response.data.gateway === 'razorpay') {
                const options = {
                    key: response.data.key,
                    amount: response.data.amount * 100,
                    currency: response.data.currency,
                    name: 'Campus Outing',
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
                            // Refresh subscription status
                            fetchCurrentSubscription();
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

    // --- Styles ---
    const S = {
        page: {
            minHeight: '100vh',
            background: '#070d1a',
            fontFamily: "'Inter', system-ui, sans-serif",
            color: '#e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            padding: '60px 24px 80px',
            position: 'relative',
            overflow: 'hidden',
        },
        glow1: {
            position: 'absolute',
            top: '-120px',
            left: '-100px',
            width: '500px',
            height: '500px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)',
            filter: 'blur(80px)',
            pointerEvents: 'none',
        },
        glow2: {
            position: 'absolute',
            bottom: '-120px',
            right: '-100px',
            width: '600px',
            height: '600px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(168,85,247,0.15) 0%, transparent 70%)',
            filter: 'blur(100px)',
            pointerEvents: 'none',
        },
        badge: {
            display: 'inline-block',
            padding: '6px 18px',
            borderRadius: '20px',
            border: '1px solid rgba(99,102,241,0.35)',
            background: 'rgba(99,102,241,0.1)',
            backdropFilter: 'blur(8px)',
            fontSize: '12px',
            fontWeight: '700',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            background: 'linear-gradient(135deg, #818cf8, #c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '20px',
        },
        heading: {
            fontSize: 'clamp(2rem, 5vw, 3.2rem)',
            fontWeight: '800',
            color: '#fff',
            marginBottom: '16px',
            lineHeight: '1.15',
        },
        headingGradient: {
            background: 'linear-gradient(135deg, #818cf8, #a78bfa, #c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
        },
        subtitle: {
            fontSize: '1.1rem',
            color: '#94a3b8',
            maxWidth: '520px',
            margin: '0 auto',
            lineHeight: '1.7',
            fontWeight: '300',
        },
        card: {
            position: 'relative',
            maxWidth: '440px',
            width: '100%',
            marginTop: '48px',
            borderRadius: '24px',
            padding: '2px',
            background: 'linear-gradient(135deg, #6366f1, #a855f7, #ec4899)',
            transition: 'transform 0.4s ease, box-shadow 0.4s ease',
            cursor: 'default',
        },
        cardHover: {
            transform: 'translateY(-6px) scale(1.01)',
            boxShadow: '0 30px 80px -20px rgba(99,102,241,0.45), 0 0 40px rgba(168,85,247,0.2)',
        },
        cardInner: {
            background: 'linear-gradient(160deg, #0e1629 0%, #0a0f1f 100%)',
            borderRadius: '22px',
            padding: '48px 40px 40px',
            position: 'relative',
            overflow: 'hidden',
        },
        innerGlow: {
            position: 'absolute',
            top: '-40px',
            right: '-40px',
            width: '160px',
            height: '160px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(99,102,241,0.3) 0%, transparent 70%)',
            filter: 'blur(40px)',
            pointerEvents: 'none',
        },
        offerBadge: {
            display: 'inline-block',
            padding: '4px 14px',
            borderRadius: '12px',
            background: 'rgba(99,102,241,0.15)',
            border: '1px solid rgba(99,102,241,0.3)',
            color: '#a5b4fc',
            fontSize: '11px',
            fontWeight: '700',
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            marginBottom: '16px',
        },
        planName: {
            fontSize: '1.6rem',
            fontWeight: '700',
            color: '#fff',
            marginBottom: '8px',
        },
        priceRow: {
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'baseline',
            gap: '6px',
            margin: '20px 0 8px',
        },
        price: {
            fontSize: '3.5rem',
            fontWeight: '800',
            background: 'linear-gradient(135deg, #c7d2fe, #fff)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            lineHeight: 1,
        },
        pricePeriod: {
            fontSize: '1.1rem',
            color: '#64748b',
            fontWeight: '500',
        },
        priceSubtext: {
            fontSize: '0.85rem',
            color: '#818cf8',
            fontWeight: '500',
            marginBottom: '32px',
        },
        featureList: {
            listStyle: 'none',
            padding: 0,
            margin: '0 0 36px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
        },
        featureItem: {
            display: 'flex',
            alignItems: 'center',
            gap: '14px',
        },
        checkIcon: {
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'rgba(99,102,241,0.15)',
            border: '1px solid rgba(99,102,241,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            boxShadow: '0 0 12px rgba(99,102,241,0.2)',
        },
        featureText: {
            fontSize: '0.95rem',
            color: '#cbd5e1',
            fontWeight: '500',
        },
        featureTextDisabled: {
            fontSize: '0.95rem',
            color: '#475569',
            fontWeight: '500',
            textDecoration: 'line-through',
        },
        disabledIcon: {
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'rgba(30,41,59,0.6)',
            border: '1px solid rgba(51,65,85,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
        },
        button: {
            width: '100%',
            padding: '16px 24px',
            borderRadius: '14px',
            border: 'none',
            fontSize: '1rem',
            fontWeight: '700',
            letterSpacing: '0.5px',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            position: 'relative',
            overflow: 'hidden',
        },
        buttonActive: {
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7)',
            color: '#fff',
            boxShadow: '0 8px 30px rgba(99,102,241,0.4)',
        },
        buttonActiveHover: {
            boxShadow: '0 12px 40px rgba(139,92,246,0.5)',
            transform: 'translateY(-2px)',
        },
        buttonDisabled: {
            background: 'rgba(30,41,59,0.7)',
            color: '#64748b',
            cursor: 'not-allowed',
            border: '1px solid rgba(51,65,85,0.5)',
            boxShadow: 'none',
        },
        securedText: {
            textAlign: 'center',
            fontSize: '0.75rem',
            color: '#475569',
            fontWeight: '500',
            marginTop: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
        },
    };

    if (!plans) {
        return (
            <div style={{ ...S.page, justifyContent: 'center' }}>
                <div style={{
                    width: '48px', height: '48px',
                    border: '3px solid rgba(99,102,241,0.3)',
                    borderTopColor: '#6366f1',
                    borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                }}></div>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    return (
        <div style={S.page}>
            {/* Background glows */}
            <div style={S.glow1}></div>
            <div style={S.glow2}></div>

            {/* Header */}
            <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', marginBottom: '8px' }}>
                <div style={S.badge}>Campus Automation</div>
                <h1 style={S.heading}>
                    Elevate Your <span style={S.headingGradient}>Experience</span>
                </h1>
                <p style={S.subtitle}>
                    Unlock limitless potential with complete outing automation.
                    Say goodbye to missed forms and hello to instant approvals.
                </p>
            </div>

            {/* Plan Card */}
            <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '30px', position: 'relative', zIndex: 1, width: '100%', maxWidth: '1000px' }}>
                {Object.entries(plans).map(([key, plan]) => {
                    const isCurrentPlan = (currentPlan?.plan_type === key || (currentPlan && currentPlan?.plan_type !== 'free')) && currentPlan?.subscription_status !== 'expired';

                    return (
                        <div
                            key={key}
                            style={{
                                ...S.card,
                                ...(hover ? S.cardHover : {}),
                            }}
                            onMouseEnter={() => setHover(true)}
                            onMouseLeave={() => setHover(false)}
                        >
                            <div style={S.cardInner}>
                                <div style={S.innerGlow}></div>

                                {/* Pricing Header */}
                                <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
                                    <div style={S.offerBadge}>✨ Special Student Offer</div>
                                    <h2 style={S.planName}>{plan.name}</h2>
                                    <div style={S.priceRow}>
                                        <span style={S.price}>₹{plan.price}</span>
                                        <span style={S.pricePeriod}>/ mo</span>
                                    </div>
                                    <p style={S.priceSubtext}>Billed monthly · Cancel anytime</p>
                                </div>

                                {/* Features */}
                                {(() => {
                                    const features = [
                                        { label: 'Unlimited Outing Form Submissions', enabled: plan.features?.monthly_submissions > 10 },
                                        { label: 'Automated Form Filling via Email', enabled: plan.features?.auto_submit },
                                        { label: 'AI-Powered PDF Data Extraction', enabled: plan.features?.auto_submit },
                                        { label: 'Auto-Generated Outing Permission PDFs', enabled: true },
                                        { label: 'Parent Notifications', enabled: plan.features?.email_notifications || plan.features?.sms_notifications },
                                        { label: 'Real-Time Submission Status Tracking', enabled: true },
                                        { label: 'Secure Outlook Credential Storage', enabled: true },
                                        { label: 'Priority Support', enabled: plan.features?.priority_support },
                                    ];
                                    return (
                                        <ul style={S.featureList}>
                                            {features.map(({ label, enabled }) => (
                                                <li key={label} style={S.featureItem}>
                                                    {enabled ? (
                                                        <div style={S.checkIcon}>
                                                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                                                <path d="M5 13l4 4L19 7" />
                                                            </svg>
                                                        </div>
                                                    ) : (
                                                        <div style={S.disabledIcon}>
                                                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#475569" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                                <path d="M6 18L18 6M6 6l12 12" />
                                                            </svg>
                                                        </div>
                                                    )}
                                                    <span style={enabled ? S.featureText : S.featureTextDisabled}>{label}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    );
                                })()}

                                {/* CTA Button */}
                                <button
                                    onClick={() => handleUpgrade(key)}
                                    disabled={isLoading || isCurrentPlan}
                                    style={{
                                        ...S.button,
                                        ...(isCurrentPlan ? S.buttonDisabled : S.buttonActive),
                                    }}
                                    onMouseEnter={e => { if (!isCurrentPlan) Object.assign(e.target.style, S.buttonActiveHover); }}
                                    onMouseLeave={e => { if (!isCurrentPlan) { e.target.style.boxShadow = S.buttonActive.boxShadow; e.target.style.transform = 'none'; } }}
                                >
                                    {isLoading ? (
                                        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 0.8s linear infinite' }}>
                                                <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="20" />
                                            </svg>
                                            Processing Securely...
                                        </span>
                                    ) : isCurrentPlan ? '✓ Current Plan Active' : '🚀 Start Automating Now'}
                                </button>

                                {/* Security note */}
                                <p style={S.securedText}>
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                    </svg>
                                    Secured by Razorpay Encryption
                                </p>
                            </div>
                        </div>
                    );
                })}
            </div>

            <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
    );
};

export default SubscriptionPlans;
