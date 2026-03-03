import React from 'react';
import { Link } from 'react-router-dom';

const Footer = () => {
    return (
        <footer className="footer-container">
            <div className="footer-grid">
                <div>
                    <h3 className="footer-section-title">🚀 Campus Outing</h3>
                    <p>Automating leave requests for campus students since 2026.</p>
                </div>
                <div>
                    <h3 className="footer-section-title">Legal</h3>
                    <ul className="footer-list">
                        <li><Link to="/privacy" className="footer-link">Privacy Policy</Link></li>
                        <li><Link to="/terms" className="footer-link">Terms & Conditions</Link></li>
                        <li><Link to="/refund-policy" className="footer-link">Cancellation/Refund Policy</Link></li>
                    </ul>
                </div>
                <div>
                    <h3 className="footer-section-title">Support</h3>
                    <ul className="footer-list">
                        <li><Link to="/contact" className="footer-link">Contact Us</Link></li>
                        <li><Link to="/plans" className="footer-link">Pricing</Link></li>
                    </ul>
                </div>
            </div>
            <div className="footer-bottom">
                <p>&copy; {new Date().getFullYear()} Campus Outing. All rights reserved.</p>
            </div>
        </footer>
    );
};

export default Footer;
