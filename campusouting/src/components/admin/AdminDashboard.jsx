import React, { useState, useEffect, useCallback, useRef } from "react";
import api from "../../utils/api";

const fmt = (d) => {
    if (!d) return "—";
    return new Date(d).toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

// ─── Skeleton Loader ─────────────────────────────────────────────────────────
const Skeleton = ({ className = "", style }) => (
    <div className={`animate-pulse bg-white/5 rounded-lg ${className}`} style={style} />
);

// ─── Toast ────────────────────────────────────────────────────────────────────
const Toast = ({ toasts, removeToast }) => (
    <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 9999, display: "flex", flexDirection: "column", gap: 10 }}>
        {toasts.map((t) => (
            <div
                key={t.id}
                onClick={() => removeToast(t.id)}
                style={{
                    background: t.type === "success" ? "rgba(16,185,129,0.15)" : t.type === "error" ? "rgba(239,68,68,0.15)" : "rgba(59,130,246,0.15)",
                    border: `1px solid ${t.type === "success" ? "rgba(16,185,129,0.4)" : t.type === "error" ? "rgba(239,68,68,0.4)" : "rgba(59,130,246,0.4)"}`,
                    color: t.type === "success" ? "#6ee7b7" : t.type === "error" ? "#fca5a5" : "#93c5fd",
                    padding: "12px 18px",
                    borderRadius: 10,
                    fontSize: 14,
                    fontFamily: "'DM Mono', monospace",
                    cursor: "pointer",
                    animation: "slideIn 0.3s ease",
                    maxWidth: 320,
                    backdropFilter: "blur(12px)",
                }}
            >
                {t.msg}
            </div>
        ))}
    </div>
);

let toastId = 0;
const useToast = () => {
    const [toasts, setToasts] = useState([]);
    const add = (msg, type = "success") => {
        const id = ++toastId;
        setToasts((p) => [...p, { id, msg, type }]);
        setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 3500);
    };
    const remove = (id) => setToasts((p) => p.filter((t) => t.id !== id));
    return { toasts, add, remove };
};

// ─── Modal ────────────────────────────────────────────────────────────────────
const Modal = ({ open, onClose, title, children }) => {
    useEffect(() => {
        const onKey = (e) => e.key === "Escape" && onClose();
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, [onClose]);

    if (!open) return null;
    return (
        <div
            onClick={onClose}
            style={{
                position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
                backdropFilter: "blur(6px)", zIndex: 9000,
                display: "flex", alignItems: "center", justifyContent: "center",
                animation: "fadeIn 0.2s ease",
            }}
        >
            <div
                onClick={(e) => e.stopPropagation()}
                style={{
                    background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
                    border: "1px solid rgba(148,163,184,0.15)",
                    borderRadius: 16,
                    padding: "32px",
                    width: "100%",
                    maxWidth: 480,
                    boxShadow: "0 40px 80px rgba(0,0,0,0.6)",
                    animation: "slideUp 0.25s ease",
                }}
            >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                    <h2 style={{ margin: 0, fontSize: 20, fontFamily: "'Space Grotesk', sans-serif", color: "#f1f5f9", fontWeight: 700 }}>{title}</h2>
                    <button onClick={onClose} style={{ background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", color: "#94a3b8", borderRadius: 8, width: 32, height: 32, cursor: "pointer", fontSize: 18, lineHeight: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>×</button>
                </div>
                {children}
            </div>
        </div>
    );
};

// ─── Field ────────────────────────────────────────────────────────────────────
const Field = ({ label, name, value, onChange, type = "text", required, children, disabled }) => (
    <div style={{ marginBottom: 16 }}>
        <label style={{ display: "block", fontSize: 12, fontFamily: "'DM Mono', monospace", color: "#64748b", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.08em" }}>{label}{required && " *"}</label>
        {children || (
            <input
                type={type}
                name={name}
                value={value}
                onChange={onChange}
                required={required}
                disabled={disabled}
                style={{
                    width: "100%", boxSizing: "border-box",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(148,163,184,0.15)",
                    borderRadius: 8,
                    color: "#f1f5f9",
                    padding: "10px 14px",
                    fontSize: 14,
                    fontFamily: "'DM Mono', monospace",
                    outline: "none",
                    transition: "border-color 0.2s",
                    opacity: disabled ? 0.5 : 1,
                }}
                onFocus={(e) => (e.target.style.borderColor = "rgba(99,102,241,0.7)")}
                onBlur={(e) => (e.target.style.borderColor = "rgba(148,163,184,0.15)")}
            />
        )}
    </div>
);

// ─── Stat Card ────────────────────────────────────────────────────────────────
const StatCard = ({ label, value, icon, accent, loading }) => (
    <div style={{
        background: "linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%)",
        border: `1px solid ${accent}30`,
        borderRadius: 14,
        padding: "22px 24px",
        position: "relative",
        overflow: "hidden",
        transition: "transform 0.2s, box-shadow 0.2s",
    }}
        onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = `0 12px 40px ${accent}20`; }}
        onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; e.currentTarget.style.boxShadow = "none"; }}
    >
        <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: 80, background: `radial-gradient(circle at top right, ${accent}20 0%, transparent 70%)` }} />
        <div style={{ fontSize: 26, marginBottom: 10 }}>{icon}</div>
        {loading ? (
            <>
                <Skeleton style={{ height: 32, width: "60%", marginBottom: 8, background: "rgba(255,255,255,0.06)", borderRadius: 6 }} />
                <Skeleton style={{ height: 16, width: "80%", background: "rgba(255,255,255,0.04)", borderRadius: 4 }} />
            </>
        ) : (
            <>
                <div style={{ fontSize: 30, fontWeight: 800, color: "#f1f5f9", fontFamily: "'Space Grotesk', sans-serif", lineHeight: 1 }}>{value}</div>
                <div style={{ fontSize: 13, color: "#64748b", marginTop: 6, fontFamily: "'DM Mono', monospace", textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
            </>
        )}
    </div>
);

// ─── Main Component ───────────────────────────────────────────────────────────
export default function AdminDashboard() {
    const { toasts, add: toast, remove: removeToast } = useToast();

    const [activeTab, setActiveTab] = useState("overview");
    const [stats, setStats] = useState(null);
    const [activity, setActivity] = useState([]);
    const [users, setUsers] = useState([]);
    const [submissions, setSubmissions] = useState([]);
    const [loadingStats, setLoadingStats] = useState(true);
    const [loadingUsers, setLoadingUsers] = useState(true);
    const [loadingActivity, setLoadingActivity] = useState(true);
    const [searchUser, setSearchUser] = useState("");
    const [filterPlan, setFilterPlan] = useState("all");
    const [filterAuto, setFilterAuto] = useState("all");
    const [selectedUser, setSelectedUser] = useState(null);

    const [userModal, setUserModal] = useState(null); // 'editPlan', 'viewPass', 'createUser'
    const [savingUser, setSavingUser] = useState(false);
    const [newUserForm, setNewUserForm] = useState({ email: '', password: '', outlook_password: '', full_name: '', roll_number: '' });

    const [formSettings, setFormSettings] = useState({ form_link: "", start_date: "", end_date: "", default_reason: "" });
    const [savingSettings, setSavingSettings] = useState(false);
    const [activityFilter, setActivityFilter] = useState("all");

    const [decryptedPassword, setDecryptedPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const intervalRef = useRef(null);

    const loadDashboard = useCallback(async () => {
        try {
            const res = await api.get('/admin/dashboard');
            setStats(res.data.stats);
            setActivity(res.data.recent_activity || []);
        } catch (e) {
            if (e.response?.status === 401 || e.response?.status === 403) window.location.href = '/admin/login';
            toast("Failed to load dashboard stats", "error");
        } finally {
            setLoadingStats(false);
            setLoadingActivity(false);
        }
    }, []);

    const loadUsers = useCallback(async () => {
        setLoadingUsers(true);
        try {
            const res = await api.get('/admin/users');
            setUsers(res.data.users || []);
        } catch (e) {
            toast("Failed to load users", "error");
        } finally {
            setLoadingUsers(false);
        }
    }, []);

    const loadConfig = useCallback(async () => {
        try {
            const res = await api.get('/config/active-outing');
            if (res.data.success) {
                setFormSettings({
                    form_link: res.data.form_link || '',
                    start_date: res.data.start_date || '',
                    end_date: res.data.end_date || '',
                    default_reason: res.data.default_reason || 'Home Visit'
                });
            }
        } catch (e) { }
    }, []);

    useEffect(() => {
        loadDashboard();
        loadUsers();
        loadConfig();
        intervalRef.current = setInterval(loadDashboard, 30000);
        return () => clearInterval(intervalRef.current);
    }, [loadDashboard, loadUsers, loadConfig]);

    // ── User Mng ──
    const openEdit = (u) => {
        setSelectedUser(u);
        setUserModal("editPlan");
    };

    const handleUpdatePlan = async (u, newPlan) => {
        if (!window.confirm(`Change plan for ${u.email} to ${newPlan.toUpperCase()}?`)) return;
        try {
            await api.post(`/admin/user/${u.id}/subscription`, { plan_type: newPlan });
            toast(`Plan updated to ${newPlan.toUpperCase()}`);
            loadUsers();
        } catch (e) {
            toast("Failed to update plan", "error");
        }
    };

    const handleToggleAutomation = async (u) => {
        try {
            await api.post(`/admin/user/${u.id}/automation`, { enabled: !u.automation_enabled });
            toast(`Automation ${!u.automation_enabled ? 'ENABLED' : 'DISABLED'} for ${u.email}`);
            loadUsers();
        } catch (e) {
            toast("Failed to toggle automation", "error");
        }
    };

    const handleViewPassword = async (u) => {
        if (!window.confirm("SECURITY WARNING: You're about to view a decrypted password. This triggers a log. Continue?")) return;
        try {
            const res = await api.get(`/admin/user/${u.id}/password`);
            setDecryptedPassword(res.data.password);
            setShowPassword(true);
            setSelectedUser(u);
            setUserModal("viewPass");
        } catch (e) {
            toast("Failed to retrieve password", "error");
        }
    };

    const handleEditUser = (u) => {
        setNewUserForm({
            email: u.email || '',
            password: '',
            outlook_password: '',
            full_name: u.full_name || '',
            roll_number: u.roll_number || ''
        });
        setUserModal('upsertUser');
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        setSavingUser(true);
        try {
            await api.post('/admin/users', newUserForm);
            toast("User saved successfully ✓");
            setUserModal(null);
            setNewUserForm({ email: '', password: '', outlook_password: '', full_name: '', roll_number: '' });
            loadUsers();
        } catch (e) {
            toast("Failed to save user: " + (e.response?.data?.error || e.message), "error");
        } finally {
            setSavingUser(false);
        }
    };

    const handleDeleteUser = async (u) => {
        if (!window.confirm(`CRITICAL WARNING: Are you sure you want to permanently delete user ${u.email} and ALL associated data? This cannot be undone.`)) return;
        try {
            await api.delete(`/admin/users/${u.id}`);
            toast("User deleted constantly ✓");
            loadUsers();
        } catch (e) {
            toast("Failed to delete user: " + (e.response?.data?.error || e.message), "error");
        }
    };

    const handleSaveSettings = async (e) => {
        e.preventDefault();
        setSavingSettings(true);
        try {
            await api.post('/admin/update-form-settings', formSettings);
            toast("Settings saved ✓");
        } catch (e) {
            toast("Save failed", "error");
        } finally {
            setSavingSettings(false);
        }
    };

    const handleSyncFromMail = async () => {
        if (!window.confirm("Fetch the latest email and overwrite current config?")) return;
        setSavingSettings(true);
        try {
            const res = await api.post('/admin/sync-config-from-mail');
            if (res.data.success) {
                toast("Synced successfully ✓");
                loadConfig();
            }
        } catch (e) {
            toast("Sync failed: " + (e.response?.data?.error || e.message), "error");
        } finally {
            setSavingSettings(false);
        }
    };

    const filteredUsers = users.filter((u) => {
        const searchMatch = u.email.toLowerCase().includes(searchUser.toLowerCase()) ||
            (u.full_name && u.full_name.toLowerCase().includes(searchUser.toLowerCase()));
        const planMatch = filterPlan === "all" || u.plan_type === filterPlan;
        const autoMatch = filterAuto === "all" || (filterAuto === "on" ? u.automation_enabled : !u.automation_enabled);
        return searchMatch && planMatch && autoMatch;
    });

    const filteredActivity = activityFilter === "all" ? activity : activity.filter((a) => a.action === activityFilter);

    // ─── Styles ───
    const S = {
        root: {
            minHeight: "100vh",
            background: "#070d1a",
            color: "#f1f5f9",
            fontFamily: "'DM Sans', sans-serif",
            backgroundImage: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.12) 0%, transparent 60%)",
        },
        header: {
            borderBottom: "1px solid rgba(148,163,184,0.08)",
            padding: "0 32px",
            height: 64,
            display: "flex", alignItems: "center", justifyContent: "space-between",
            background: "rgba(7,13,26,0.8)", backdropFilter: "blur(20px)",
            position: "sticky", top: 0, zIndex: 100,
        },
        logo: {
            fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20,
            background: "linear-gradient(135deg, #818cf8 0%, #c084fc 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            letterSpacing: "-0.02em",
        },
        badge: (color) => ({
            display: "inline-flex", alignItems: "center", gap: 5, padding: "3px 10px",
            borderRadius: 20, fontSize: 11, fontFamily: "'DM Mono', monospace", fontWeight: 600,
            textTransform: "uppercase", letterSpacing: "0.06em", ...color,
        }),
        tabs: { display: "flex", gap: 2, padding: "16px 32px 0", borderBottom: "1px solid rgba(148,163,184,0.08)" },
        tab: (active) => ({
            padding: "10px 18px", fontSize: 13, fontFamily: "'DM Mono', monospace", cursor: "pointer",
            border: "none", background: "transparent", color: active ? "#818cf8" : "#475569",
            borderBottom: active ? "2px solid #818cf8" : "2px solid transparent",
            transition: "all 0.2s", fontWeight: active ? 700 : 400, textTransform: "uppercase", letterSpacing: "0.06em",
        }),
        content: { padding: "28px 32px" },
        sectionTitle: {
            fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 700, color: "#f1f5f9",
            margin: "0 0 16px", letterSpacing: "-0.01em",
        },
        card: {
            background: "rgba(255,255,255,0.03)", border: "1px solid rgba(148,163,184,0.1)", borderRadius: 14, overflow: "hidden",
        },
        btn: (variant = "primary") => ({
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: variant === "icon" ? "8px" : "9px 16px", borderRadius: 8, fontSize: 13,
            fontFamily: "'DM Mono', monospace", fontWeight: 600, cursor: "pointer",
            border: "1px solid", transition: "all 0.15s",
            ...(variant === "primary" ? {
                background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)", borderColor: "transparent", color: "#fff", boxShadow: "0 4px 15px rgba(99,102,241,0.3)",
            } : variant === "action" ? {
                background: "rgba(99,102,241,0.1)", borderColor: "rgba(99,102,241,0.3)", color: "#a5b4fc",
            } : variant === "danger" ? {
                background: "rgba(239,68,68,0.1)", borderColor: "rgba(239,68,68,0.3)", color: "#fca5a5",
            } : variant === "ghost" ? {
                background: "rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.08)", color: "#94a3b8",
            } : variant === "warning" ? {
                background: "rgba(245,158,11,0.1)", borderColor: "rgba(245,158,11,0.3)", color: "#fcd34d",
            } : {
                background: "rgba(255,255,255,0.04)", borderColor: "rgba(148,163,184,0.15)", color: "#94a3b8",
            }),
        }),
        input: {
            background: "rgba(255,255,255,0.04)", border: "1px solid rgba(148,163,184,0.15)", borderRadius: 8, color: "#f1f5f9",
            padding: "9px 14px", fontSize: 13, fontFamily: "'DM Mono', monospace", outline: "none",
        },
        select: {
            background: "rgba(255,255,255,0.04)", border: "1px solid rgba(148,163,184,0.15)", borderRadius: 8, color: "#94a3b8",
            padding: "9px 12px", fontSize: 13, fontFamily: "'DM Mono', monospace", outline: "none", cursor: "pointer",
        },
        th: {
            padding: "12px 16px", fontSize: 11, fontFamily: "'DM Mono', monospace", textTransform: "uppercase",
            letterSpacing: "0.1em", color: "#475569", background: "rgba(0,0,0,0.2)", textAlign: "left", fontWeight: 700,
        },
        td: { padding: "14px 16px", borderBottom: "1px solid rgba(148,163,184,0.06)", fontSize: 13, verticalAlign: "middle" },
    };

    const planBadge = (p) => {
        if (p === "premium") return S.badge({ background: "rgba(192,132,252,0.12)", color: "#e879f9", border: "1px solid rgba(192,132,252,0.25)" });
        if (p === "basic") return S.badge({ background: "rgba(56,189,248,0.12)", color: "#7dd3fc", border: "1px solid rgba(56,189,248,0.25)" });
        return S.badge({ background: "rgba(148,163,184,0.12)", color: "#cbd5e1", border: "1px solid rgba(148,163,184,0.25)" });
    };

    const autoBadge = (a) => a
        ? S.badge({ background: "rgba(16,185,129,0.12)", color: "#6ee7b7", border: "1px solid rgba(16,185,129,0.2)" })
        : S.badge({ background: "rgba(239,68,68,0.12)", color: "#fca5a5", border: "1px solid rgba(239,68,68,0.2)" });

    return (
        <>
            <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
            <style>{`
        * { box-sizing: border-box; }
        body { margin: 0; }
        @keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
        @keyframes slideUp { from { transform: translateY(20px); opacity: 0 } to { transform: translateY(0); opacity: 1 } }
        @keyframes slideIn { from { transform: translateX(20px); opacity: 0 } to { transform: translateX(0); opacity: 1 } }
        @keyframes pulse { 0%,100% { opacity: 1 } 50% { opacity: 0.4 } }
        .animate-pulse { animation: pulse 1.8s ease infinite; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.15); border-radius: 3px; }
        button:hover { opacity: 0.88; }
        input::placeholder { color: #475569; }
        tr:hover td { background: rgba(255,255,255,0.02); }
      `}</style>

            <div style={S.root}>
                <header style={S.header}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #6366f1, #c084fc)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>⚡</div>
                        <span style={S.logo}>CampusAdmin</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                        <button style={S.btn("ghost")} onClick={() => { localStorage.clear(); window.location.href = '/login'; }}>Logout</button>
                        <div style={{ width: 34, height: 34, borderRadius: "50%", background: "linear-gradient(135deg, #6366f1, #c084fc)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, color: "#fff", fontWeight: 700 }}>A</div>
                    </div>
                </header>

                <nav style={S.tabs}>
                    {[["overview", "📊 Overview"], ["users", "👥 Users"], ["activity", "📋 Logs"], ["settings", "⚙️ Settings"]].map(([k, label]) => (
                        <button key={k} style={S.tab(activeTab === k)} onClick={() => setActiveTab(k)}>{label}</button>
                    ))}
                </nav>

                <main style={S.content}>
                    {activeTab === "overview" && (
                        <div style={{ animation: "slideUp 0.3s ease" }}>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 28 }}>
                                {[
                                    { label: "Total Users", value: stats?.total_users ?? "—", icon: "👥", accent: "#818cf8" },
                                    { label: "Revenue", value: stats?.total_revenue ? `₹${stats.total_revenue}` : "—", icon: "💰", accent: "#10b981" },
                                    { label: "Submissions", value: stats?.total_submissions ?? "—", icon: "📤", accent: "#f59e0b" },
                                    { label: "Queue Sizes", value: stats?.queue_size ?? "—", icon: "⚡", accent: "#c084fc" },
                                ].map((s) => <StatCard key={s.label} {...s} loading={loadingStats} />)}
                            </div>

                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
                                <h2 style={S.sectionTitle}>Recent Context</h2>
                                <button style={S.btn("ghost")} onClick={() => setActiveTab("activity")}>View all →</button>
                            </div>
                            <div style={S.card}>
                                {loadingActivity ? (
                                    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                                        {[...Array(4)].map((_, i) => <Skeleton key={i} style={{ height: 44, background: "rgba(255,255,255,0.04)", borderRadius: 8, animationDelay: `${i * 0.1}s` }} />)}
                                    </div>
                                ) : (
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                            <tr>{["User", "Status", "Description", "Time"].map((h) => <th key={h} style={S.th}>{h}</th>)}</tr>
                                        </thead>
                                        <tbody>
                                            {activity.slice(0, 8).map((a, i) => (
                                                <tr key={i}>
                                                    <td style={{ ...S.td, fontFamily: "'DM Mono', monospace", fontSize: 12, color: "#94a3b8" }}>{a.email}</td>
                                                    <td style={S.td}>
                                                        <span style={a.action === "COMPLETED" ? S.badge({ background: "rgba(16,185,129,0.1)", color: "#6ee7b7", border: "1px solid rgba(16,185,129,0.25)" }) : S.badge({ background: "rgba(239,68,68,0.1)", color: "#fca5a5", border: "1px solid rgba(239,68,68,0.25)" })}>
                                                            {a.action === "COMPLETED" ? "✓ " : "✗ "}{a.action}
                                                        </span>
                                                    </td>
                                                    <td style={{ ...S.td, color: "#64748b", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.description}</td>
                                                    <td style={{ ...S.td, fontFamily: "'DM Mono', monospace", fontSize: 11, color: "#475569" }}>{fmt(a.created_at)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === "users" && (
                        <div style={{ animation: "slideUp 0.3s ease" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
                                <input placeholder="Search user..." value={searchUser} onChange={(e) => setSearchUser(e.target.value)} style={{ ...S.input, flex: 1, minWidth: 220 }} />
                                <select value={filterPlan} onChange={(e) => setFilterPlan(e.target.value)} style={S.select}>
                                    <option value="all">All Plans</option>
                                    <option value="free">Free</option>
                                    <option value="basic">Basic</option>
                                    <option value="premium">Premium</option>
                                </select>
                                <select value={filterAuto} onChange={(e) => setFilterAuto(e.target.value)} style={S.select}>
                                    <option value="all">All Status</option>
                                    <option value="on">Auto ON</option>
                                    <option value="off">Auto OFF</option>
                                </select>
                                <button style={S.btn("primary")} onClick={() => { setNewUserForm({ email: '', password: '', outlook_password: '', full_name: '', roll_number: '' }); setUserModal('upsertUser'); }}>+ Add User</button>
                                <button style={S.btn("ghost")} onClick={loadUsers}>↻</button>
                            </div>

                            <div style={S.card}>
                                {loadingUsers ? (
                                    <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 12 }}>
                                        {[...Array(5)].map((_, i) => <Skeleton key={i} style={{ height: 48, background: "rgba(255,255,255,0.04)", borderRadius: 8 }} />)}
                                    </div>
                                ) : filteredUsers.length === 0 ? (
                                    <div style={{ padding: 60, textAlign: "center", color: "#475569", fontFamily: "'DM Mono', monospace" }}>No users match your filters</div>
                                ) : (
                                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                        <thead>
                                            <tr>{["Name/Email", "Plan", "Automation", "Tools"].map((h) => <th key={h} style={S.th}>{h}</th>)}</tr>
                                        </thead>
                                        <tbody>
                                            {filteredUsers.map((u) => (
                                                <tr key={u.id}>
                                                    <td style={S.td}>
                                                        <div style={{ fontWeight: 600 }}>{u.full_name || 'N/A'}</div>
                                                        <div style={{ fontSize: 11, color: "#64748b", fontFamily: "'DM Mono', monospace" }}>{u.email}</div>
                                                    </td>
                                                    <td style={S.td}>
                                                        <span style={planBadge(u.plan_type || 'free')}>
                                                            {(u.plan_type || 'free').toUpperCase()}
                                                        </span>
                                                    </td>
                                                    <td style={S.td}>
                                                        <span style={autoBadge(u.automation_enabled)}>
                                                            {u.automation_enabled ? 'Auto ON' : 'Auto OFF'}
                                                        </span>
                                                    </td>
                                                    <td style={S.td}>
                                                        <div style={{ display: "flex", gap: 6 }}>
                                                            <button style={S.btn("ghost")} onClick={() => handleEditUser(u)}>Edit</button>
                                                            <button style={S.btn("action")} onClick={() => handleToggleAutomation(u)}>{u.automation_enabled ? "Disable Auto" : "Enable Auto"}</button>
                                                            <button style={S.btn("ghost")} onClick={() => handleUpdatePlan(u, 'free')}>Free</button>
                                                            <button style={S.btn("ghost")} onClick={() => handleUpdatePlan(u, 'basic')}>Basic</button>
                                                            <button style={S.btn("ghost")} onClick={() => handleUpdatePlan(u, 'premium')}>Premium</button>
                                                            <button style={S.btn("danger")} onClick={() => handleViewPassword(u)}>Pass</button>
                                                            <button style={{ ...S.btn("danger"), background: "rgba(220,38,38,0.2)", borderColor: "rgba(239,68,68,0.5)", color: "#f87171" }} onClick={() => handleDeleteUser(u)}>Delete</button>
                                                        </div>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === "activity" && (
                        <div style={{ animation: "slideUp 0.3s ease" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
                                <h2 style={{ ...S.sectionTitle, margin: 0, flex: 1 }}>Activity Logs</h2>
                                {["all", "COMPLETED", "FAILED"].map((f) => (
                                    <button key={f} style={S.btn(activityFilter === f ? "primary" : "ghost")} onClick={() => setActivityFilter(f)}>
                                        {f === "all" ? "All" : f}
                                    </button>
                                ))}
                            </div>
                            <div style={S.card}>
                                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                    <thead>
                                        <tr>{["User", "Status", "Description", "Time"].map((h) => <th key={h} style={S.th}>{h}</th>)}</tr>
                                    </thead>
                                    <tbody>
                                        {filteredActivity.map((a, i) => (
                                            <tr key={i}>
                                                <td style={{ ...S.td, fontFamily: "'DM Mono', monospace", fontSize: 12 }}>{a.email}</td>
                                                <td style={S.td}>
                                                    <span style={a.action === "COMPLETED" ? S.badge({ background: "rgba(16,185,129,0.1)", color: "#6ee7b7", border: "1px solid rgba(16,185,129,0.25)" }) : S.badge({ background: "rgba(239,68,68,0.1)", color: "#fca5a5", border: "1px solid rgba(239,68,68,0.25)" })}>
                                                        {a.action}
                                                    </span>
                                                </td>
                                                <td style={{ ...S.td, color: "#64748b" }}>{a.description}</td>
                                                <td style={{ ...S.td, fontFamily: "'DM Mono', monospace", fontSize: 11, color: "#475569" }}>{fmt(a.created_at)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {activeTab === "settings" && (
                        <div style={{ animation: "slideUp 0.3s ease", maxWidth: 600 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                                <h2 style={S.sectionTitle}>Form Settings</h2>
                                <button style={S.btn("action")} onClick={handleSyncFromMail}>✉️ Sync from Mail</button>
                            </div>
                            <div style={{ ...S.card, padding: 28 }}>
                                <form onSubmit={handleSaveSettings}>
                                    <Field label="MS Form Link" name="form_link" value={formSettings.form_link} required onChange={(e) => setFormSettings((p) => ({ ...p, form_link: e.target.value }))} />
                                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                                        <Field label="Start Date" name="start_date" type="date" value={formSettings.start_date} onChange={(e) => setFormSettings((p) => ({ ...p, start_date: e.target.value }))} />
                                        <Field label="End Date" name="end_date" type="date" value={formSettings.end_date} onChange={(e) => setFormSettings((p) => ({ ...p, end_date: e.target.value }))} />
                                    </div>
                                    <Field label="Default Reason" name="default_reason" value={formSettings.default_reason || ""} onChange={(e) => setFormSettings((p) => ({ ...p, default_reason: e.target.value }))} />
                                    <div style={{ marginTop: 8 }}>
                                        <button type="submit" style={S.btn("primary")} disabled={savingSettings}>
                                            {savingSettings ? "Saving…" : "💾 Save Settings"}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    )}
                </main>
            </div>

            <Modal open={userModal === "viewPass"} onClose={() => { setUserModal(null); setShowPassword(false); }} title="Decrypted Password">
                <div style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>
                    Password for <strong style={{ color: "#f1f5f9" }}>{selectedUser?.email}</strong>:
                </div>
                <code style={{ display: 'block', padding: 16, background: 'rgba(239,68,68,0.1)', color: '#fca5a5', borderRadius: 8, fontSize: 18, fontFamily: "'DM Mono', monospace", textAlign: 'center', marginBottom: 24 }}>
                    {decryptedPassword}
                </code>
                <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                    <button onClick={() => { setUserModal(null); setShowPassword(false); }} style={S.btn("primary")}>Close</button>
                </div>
            </Modal>

            <Modal open={userModal === "upsertUser"} onClose={() => setUserModal(null)} title="Create / Edit User">
                <form onSubmit={handleCreateUser}>
                    <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>
                        Note: For existing users, only the filled fields will be updated. Passwords can be left blank if you don't want to change them.
                    </p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                        <Field label="Full Name" name="full_name" value={newUserForm.full_name} required onChange={e => setNewUserForm(p => ({ ...p, full_name: e.target.value }))} />
                        <Field label="Roll Number" name="roll_number" value={newUserForm.roll_number} required onChange={e => setNewUserForm(p => ({ ...p, roll_number: e.target.value }))} />
                    </div>
                    <Field label="Email Address" type="email" name="email" value={newUserForm.email} required onChange={e => setNewUserForm(p => ({ ...p, email: e.target.value }))} />
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                        <Field label="App Password" name="password" type="password" value={newUserForm.password} onChange={e => setNewUserForm(p => ({ ...p, password: e.target.value }))} />
                        <Field label="Outlook Password" name="outlook_password" type="password" value={newUserForm.outlook_password} onChange={e => setNewUserForm(p => ({ ...p, outlook_password: e.target.value }))} />
                    </div>
                    <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                        <button type="button" onClick={() => setUserModal(null)} style={S.btn("ghost")}>Cancel</button>
                        <button type="submit" style={S.btn("primary")} disabled={savingUser}>
                            {savingUser ? "Saving..." : "Save User"}
                        </button>
                    </div>
                </form>
            </Modal>

            <Toast toasts={toasts} removeToast={removeToast} />
        </>
    );
}
