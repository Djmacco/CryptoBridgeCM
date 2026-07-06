import { useState, useEffect, useCallback } from "react"

// ─── DESIGN TOKENS ────────────────────────────────────────────────────────────
const T = {
  // Brand palette — deep midnight blue with amber gold accent
  bg:        "#080b14",
  surface:   "#0e1220",
  card:      "#131826",
  cardHover: "#171d2e",
  border:    "#1e2640",
  borderHi:  "#2a3555",

  // Brand accent: amber gold
  gold:      "#f0a500",
  goldDim:   "#b87800",
  goldBg:    "#1a1200",
  goldBorder:"#3d2e00",

  // Status colors
  green:     "#00c896",
  greenBg:   "#001a12",
  greenBorder:"#00442e",
  red:       "#ff4d6a",
  redBg:     "#1a0008",
  redBorder: "#44001a",
  blue:      "#4d9fff",
  blueBg:    "#00101a",
  blueBorder:"#00284d",
  orange:    "#ff8c42",
  orangeBg:  "#1a0a00",

  // Text
  text:      "#e8eaf2",
  dim:       "#8891a8",
  muted:     "#4a5268",

  // Fonts
  sans:      "'Inter', 'DM Sans', system-ui, sans-serif",
  mono:      "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', monospace",
}

// ─── MOCK API ─────────────────────────────────────────────────────────────────
const API_BASE = "http://localhost:5000/api"
let authToken = null

const api = async (method, path, body = null) => {
  const headers = { "Content-Type": "application/json", "X-Dev-Mode": "true" }
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data.error || "Request failed")
  return data.data
}

// ─── ICONS ────────────────────────────────────────────────────────────────────
const Icon = ({ name, size = 20, color = "currentColor" }) => {
  const paths = {
    home: "M3 9.5L12 3l9 6.5V21H15v-5h-6v5H3V9.5z",
    wallet: "M21 4H3a1 1 0 00-1 1v14a1 1 0 001 1h18a1 1 0 001-1V5a1 1 0 00-1-1zm-1 8H16a2 2 0 110-4h4v4z",
    trade: "M7 16l-4-4 4-4M17 8l4 4-4 4M14 4l-4 16",
    user: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z",
    chat: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z",
    copy: "M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2v-2M8 4h8l4 4v8a2 2 0 01-2 2H8M8 4a2 2 0 00-2 2v2",
    check: "M20 6L9 17l-5-5",
    x: "M18 6L6 18M6 6l12 12",
    arrow: "M5 12h14M12 5l7 7-7 7",
    shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
    alert: "M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01",
    send: "M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z",
    eye: "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8zM12 12a3 3 0 100-6 3 3 0 000 6z",
    eyeOff: "M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24M1 1l22 22",
    lock: "M19 11H5a2 2 0 00-2 2v7a2 2 0 002 2h14a2 2 0 002-2v-7a2 2 0 00-2-2zM7 11V7a5 5 0 0110 0v4",
    trending: "M23 6l-9.5 9.5-5-5L1 18",
    plus: "M12 5v14M5 12h14",
    logout: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9",
    settings: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z",
    refresh: "M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15",
    bot: "M12 2a2 2 0 012 2c0 .74-.4 1.39-1 1.73V7h3a3 3 0 013 3v8a3 3 0 01-3 3H6a3 3 0 01-3-3v-8a3 3 0 013-3h3V5.73c-.6-.34-1-.99-1-1.73a2 2 0 012-2zM9 14a1 1 0 100-2 1 1 0 000 2zM15 14a1 1 0 100-2 1 1 0 000 2z",
    qr: "M3 3h6v6H3zM15 3h6v6h-6zM3 15h6v6H3zM15 15h2v2h-2zM19 15v2M15 19h4M19 19v2",
  }
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke={color} strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d={paths[name] || ""} />
    </svg>
  )
}

// ─── UI PRIMITIVES ────────────────────────────────────────────────────────────
const Btn = ({ children, onClick, variant = "primary", size = "md", disabled, fullWidth, style }) => {
  const base = {
    display: "inline-flex", alignItems: "center", justifyContent: "center",
    gap: 8, border: "none", borderRadius: 10, cursor: disabled ? "not-allowed" : "pointer",
    fontFamily: T.sans, fontWeight: 600, letterSpacing: "0.01em",
    transition: "all 0.15s", opacity: disabled ? 0.5 : 1,
    width: fullWidth ? "100%" : "auto",
    ...style,
  }
  const sizes = {
    sm: { padding: "7px 14px", fontSize: 13 },
    md: { padding: "11px 20px", fontSize: 14 },
    lg: { padding: "14px 28px", fontSize: 16 },
  }
  const variants = {
    primary:   { background: T.gold, color: "#000", boxShadow: `0 0 20px ${T.gold}30` },
    secondary: { background: T.card, color: T.text, border: `1px solid ${T.border}` },
    danger:    { background: T.redBg, color: T.red, border: `1px solid ${T.redBorder}` },
    ghost:     { background: "transparent", color: T.dim, border: `1px solid ${T.border}` },
    success:   { background: T.greenBg, color: T.green, border: `1px solid ${T.greenBorder}` },
  }
  return (
    <button onClick={!disabled ? onClick : undefined}
      style={{ ...base, ...sizes[size], ...variants[variant] }}>
      {children}
    </button>
  )
}

const Input = ({ label, value, onChange, type = "text", placeholder, error, prefix, suffix, hint }) => (
  <div style={{ marginBottom: 16 }}>
    {label && <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: T.dim, marginBottom: 6, letterSpacing: "0.04em", textTransform: "uppercase" }}>{label}</label>}
    <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
      {prefix && <span style={{ position: "absolute", left: 12, color: T.dim, fontSize: 14, pointerEvents: "none", zIndex: 1 }}>{prefix}</span>}
      <input value={value} onChange={e => onChange(e.target.value)} type={type} placeholder={placeholder}
        style={{
          width: "100%", background: T.surface, border: `1px solid ${error ? T.redBorder : T.border}`,
          borderRadius: 10, color: T.text, fontFamily: T.sans, fontSize: 15, outline: "none",
          padding: prefix ? "11px 12px 11px 36px" : suffix ? "11px 40px 11px 14px" : "11px 14px",
          transition: "border-color 0.15s", boxSizing: "border-box",
        }}
        onFocus={e => e.target.style.borderColor = T.gold}
        onBlur={e => e.target.style.borderColor = error ? T.redBorder : T.border}
      />
      {suffix && <span style={{ position: "absolute", right: 12, color: T.dim }}>{suffix}</span>}
    </div>
    {error && <p style={{ fontSize: 12, color: T.red, marginTop: 4 }}>{error}</p>}
    {hint && !error && <p style={{ fontSize: 12, color: T.muted, marginTop: 4 }}>{hint}</p>}
  </div>
)

const Card = ({ children, style, onClick, hover }) => {
  const [hovered, setHovered] = useState(false)
  return (
    <div onClick={onClick}
      onMouseEnter={() => hover && setHovered(true)}
      onMouseLeave={() => hover && setHovered(false)}
      style={{
        background: hovered ? T.cardHover : T.card,
        border: `1px solid ${hovered ? T.borderHi : T.border}`,
        borderRadius: 14, padding: 20, transition: "all 0.15s",
        cursor: onClick ? "pointer" : "default", ...style,
      }}>
      {children}
    </div>
  )
}

const Badge = ({ children, color = T.gold, bg }) => (
  <span style={{
    background: bg || `${color}18`, color, border: `1px solid ${color}33`,
    borderRadius: 6, padding: "3px 10px", fontSize: 12, fontWeight: 700,
    fontFamily: T.mono, letterSpacing: "0.04em", display: "inline-flex", alignItems: "center",
  }}>{children}</span>
)

const Toast = ({ msg, type = "success", onDismiss }) => {
  useEffect(() => { const t = setTimeout(onDismiss, 3500); return () => clearTimeout(t) }, [])
  const colors = { success: T.green, error: T.red, info: T.blue, warn: T.orange }
  return (
    <div style={{
      position: "fixed", bottom: 80, left: "50%", transform: "translateX(-50%)",
      background: T.card, border: `1px solid ${colors[type]}44`, borderRadius: 12,
      padding: "12px 20px", color: T.text, fontSize: 14, fontWeight: 500,
      boxShadow: `0 8px 32px #000a, 0 0 0 1px ${colors[type]}22`,
      zIndex: 9999, maxWidth: 340, textAlign: "center",
      animation: "slideUp 0.2s ease",
    }}>
      <span style={{ color: colors[type], marginRight: 8 }}>
        {type === "success" ? "✓" : type === "error" ? "✕" : "ℹ"}
      </span>
      {msg}
    </div>
  )
}

const Spinner = ({ size = 24, color = T.gold }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{ animation: "spin 0.8s linear infinite" }}>
    <circle cx="12" cy="12" r="10" fill="none" stroke={`${color}30`} strokeWidth="3" />
    <path d="M12 2a10 10 0 0110 10" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" />
  </svg>
)

const StatusBadge = ({ status }) => {
  const map = {
    CREATED:         { label: "Open", color: T.blue },
    MATCHED:         { label: "Matched", color: T.orange },
    PAYMENT_PENDING: { label: "Awaiting Payment", color: T.orange },
    PAID:            { label: "Paid", color: T.green },
    RELEASING:       { label: "Releasing", color: T.green },
    COMPLETED:       { label: "Completed", color: T.green },
    CANCELLED:       { label: "Cancelled", color: T.muted },
    DISPUTED:        { label: "Disputed", color: T.red },
    RESOLVED:        { label: "Resolved", color: T.dim },
    REVERSED:        { label: "Reversed", color: T.red },
  }
  const s = map[status] || { label: status, color: T.dim }
  return <Badge color={s.color}>{s.label}</Badge>
}

// ─── COUNTDOWN TIMER ──────────────────────────────────────────────────────────
const Countdown = ({ deadline, onExpire }) => {
  const calc = () => Math.max(0, Math.floor((new Date(deadline) - Date.now()) / 1000))
  const [secs, setSecs] = useState(calc)

  useEffect(() => {
    if (!deadline) return
    const t = setInterval(() => {
      const r = calc()
      setSecs(r)
      if (r === 0 && onExpire) onExpire()
    }, 1000)
    return () => clearInterval(t)
  }, [deadline])

  const m = Math.floor(secs / 60), s = secs % 60
  const pct = deadline ? Math.min(100, (secs / 1800) * 100) : 0
  const urgent = secs < 300

  return (
    <div style={{ textAlign: "center" }}>
      <div style={{ fontFamily: T.mono, fontSize: 36, fontWeight: 700, color: urgent ? T.red : T.gold, letterSpacing: "0.05em" }}>
        {String(m).padStart(2, "0")}:{String(s).padStart(2, "0")}
      </div>
      <div style={{ height: 4, background: T.border, borderRadius: 2, marginTop: 8, overflow: "hidden" }}>
        <div style={{
          height: "100%", borderRadius: 2,
          background: urgent ? T.red : T.gold,
          width: `${pct}%`, transition: "width 1s linear"
        }} />
      </div>
      <p style={{ fontSize: 12, color: T.muted, marginTop: 6 }}>
        {secs === 0 ? "Expired" : "Time remaining to pay"}
      </p>
    </div>
  )
}

// ─── BALANCE CARD ─────────────────────────────────────────────────────────────
const BalanceCard = ({ balance, onDeposit, onWithdraw }) => {
  const fmt = (raw) => (raw / 1_000_000).toFixed(2)
  return (
    <Card style={{ background: `linear-gradient(135deg, #0e1a30 0%, #131826 100%)`, border: `1px solid ${T.borderHi}`, position: "relative", overflow: "hidden" }}>
      {/* Decorative circle */}
      <div style={{ position: "absolute", top: -40, right: -40, width: 160, height: 160, borderRadius: "50%", background: `${T.gold}08`, border: `1px solid ${T.gold}12`, pointerEvents: "none" }} />
      <div style={{ position: "absolute", top: 20, right: 20, width: 80, height: 80, borderRadius: "50%", background: `${T.gold}06`, pointerEvents: "none" }} />

      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: 20 }}>
        <div>
          <p style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 4 }}>Total Balance</p>
          <p style={{ fontSize: 32, fontWeight: 800, color: T.text, fontFamily: T.mono, letterSpacing: "-0.02em" }}>
            {balance ? fmt(balance.total.raw) : "—"}
            <span style={{ fontSize: 16, color: T.dim, marginLeft: 6 }}>USDT</span>
          </p>
        </div>
        <div style={{ background: `${T.gold}15`, border: `1px solid ${T.gold}30`, borderRadius: 10, padding: "8px 10px" }}>
          <Icon name="wallet" color={T.gold} size={22} />
        </div>
      </div>

      {balance && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 20 }}>
          {[
            { label: "Available", val: balance.available.raw, color: T.green },
            { label: "In Escrow", val: balance.locked.raw, color: T.orange },
            { label: "On Hold", val: balance.hold.raw, color: T.blue },
          ].map(b => (
            <div key={b.label} style={{ background: `${b.color}08`, border: `1px solid ${b.color}18`, borderRadius: 8, padding: "10px 10px 8px" }}>
              <p style={{ fontSize: 11, color: b.color, fontWeight: 600, marginBottom: 4, letterSpacing: "0.04em" }}>{b.label}</p>
              <p style={{ fontFamily: T.mono, fontSize: 14, fontWeight: 700, color: T.text }}>{fmt(b.val)}</p>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 10 }}>
        <Btn onClick={onDeposit} size="sm" style={{ flex: 1 }}>
          <Icon name="plus" size={15} /> Deposit
        </Btn>
        <Btn onClick={onWithdraw} variant="secondary" size="sm" style={{ flex: 1 }}>
          <Icon name="send" size={15} /> Withdraw
        </Btn>
      </div>
    </Card>
  )
}

// ─── CHAT WIDGET ──────────────────────────────────────────────────────────────
const ChatWidget = ({ language }) => {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState([{
    role: "bot",
    text: language === "fr"
      ? "Bonjour ! Je suis CryptoBot 🤖\nComment puis-je vous aider ?"
      : "Hello! I'm CryptoBot 🤖\nHow can I help you today?",
  }])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [quickReplies, setQuickReplies] = useState([])
  const bottomRef = useRef ? null : null
  const msgEnd = { current: null }

  useEffect(() => {
    fetch(`${API_BASE}/chat/quick-replies?lang=${language}`)
      .then(r => r.json())
      .then(d => setQuickReplies(d.data?.quick_replies || []))
      .catch(() => {})
  }, [language])

  const send = async (text) => {
    if (!text.trim() || loading) return
    const userMsg = { role: "user", text }
    setMsgs(m => [...m, userMsg])
    setInput("")
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json()
      setMsgs(m => [...m, { role: "bot", text: data.data?.response || "...", scam: data.data?.scam_alert }])
    } catch {
      setMsgs(m => [...m, { role: "bot", text: language === "fr" ? "Service temporairement indisponible." : "Service temporarily unavailable." }])
    }
    setLoading(false)
  }

  return (
    <>
      {/* Floating button */}
      <button onClick={() => setOpen(o => !o)} style={{
        position: "fixed", bottom: 84, right: 20, width: 52, height: 52,
        borderRadius: "50%", background: T.gold, border: "none", cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        boxShadow: `0 4px 20px ${T.gold}50`, zIndex: 1000,
        transition: "transform 0.2s", transform: open ? "scale(0.9)" : "scale(1)",
      }}>
        <Icon name={open ? "x" : "bot"} color="#000" size={22} />
      </button>

      {/* Chat panel */}
      {open && (
        <div style={{
          position: "fixed", bottom: 150, right: 20, width: 320, height: 480,
          background: T.surface, border: `1px solid ${T.border}`, borderRadius: 16,
          display: "flex", flexDirection: "column", zIndex: 999,
          boxShadow: "0 20px 60px #000a",
        }}>
          {/* Header */}
          <div style={{ padding: "14px 16px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: `${T.gold}20`, border: `1px solid ${T.gold}40`, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name="bot" color={T.gold} size={18} />
            </div>
            <div>
              <p style={{ fontWeight: 700, fontSize: 14, color: T.text }}>CryptoBot</p>
              <p style={{ fontSize: 11, color: T.green }}>● Online</p>
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: 12, display: "flex", flexDirection: "column", gap: 10 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
                <div style={{
                  maxWidth: "85%",
                  background: m.role === "user" ? T.gold : m.scam ? T.redBg : T.card,
                  color: m.role === "user" ? "#000" : T.text,
                  border: m.scam ? `1px solid ${T.redBorder}` : "none",
                  borderRadius: m.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                  padding: "10px 13px", fontSize: 13, lineHeight: 1.55, whiteSpace: "pre-wrap",
                }}>
                  {m.text}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", gap: 4, padding: "8px 12px" }}>
                {[0,1,2].map(i => <div key={i} style={{ width: 7, height: 7, borderRadius: "50%", background: T.dim, animation: `pulse 1s ${i*0.2}s infinite` }} />)}
              </div>
            )}
          </div>

          {/* Quick replies */}
          {msgs.length === 1 && quickReplies.length > 0 && (
            <div style={{ padding: "0 10px 8px", display: "flex", flexWrap: "wrap", gap: 6 }}>
              {quickReplies.slice(0, 4).map(qr => (
                <button key={qr.id} onClick={() => send(qr.label.replace(/^[^\s]+\s/, ''))}
                  style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: 20, padding: "5px 10px", fontSize: 11, color: T.dim, cursor: "pointer", fontFamily: T.sans }}>
                  {qr.label}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{ padding: 10, borderTop: `1px solid ${T.border}`, display: "flex", gap: 8 }}>
            <input value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && send(input)}
              placeholder={language === "fr" ? "Votre question..." : "Your question..."}
              style={{ flex: 1, background: T.card, border: `1px solid ${T.border}`, borderRadius: 20, padding: "8px 14px", color: T.text, fontSize: 13, outline: "none", fontFamily: T.sans }}
            />
            <button onClick={() => send(input)} style={{ width: 36, height: 36, borderRadius: "50%", background: T.gold, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name="send" color="#000" size={15} />
            </button>
          </div>
        </div>
      )}
    </>
  )
}

// ─── BOTTOM NAV ───────────────────────────────────────────────────────────────
const BottomNav = ({ page, setPage }) => {
  const items = [
    { id: "dashboard", icon: "home", label: "Home" },
    { id: "wallet", icon: "wallet", label: "Wallet" },
    { id: "trades", icon: "trade", label: "Trades" },
    { id: "profile", icon: "user", label: "Profile" },
  ]
  return (
    <nav style={{
      position: "fixed", bottom: 0, left: 0, right: 0,
      background: T.surface, borderTop: `1px solid ${T.border}`,
      display: "flex", padding: "8px 0 12px", zIndex: 100,
    }}>
      {items.map(item => {
        const active = page === item.id
        return (
          <button key={item.id} onClick={() => setPage(item.id)} style={{
            flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4,
            background: "none", border: "none", cursor: "pointer",
            color: active ? T.gold : T.muted, transition: "color 0.15s",
          }}>
            {active && <div style={{ position: "absolute", width: 4, height: 4, borderRadius: "50%", background: T.gold, marginTop: -8 }} />}
            <Icon name={item.icon} size={22} color={active ? T.gold : T.muted} />
            <span style={{ fontSize: 10, fontWeight: active ? 700 : 500, letterSpacing: "0.04em" }}>{item.label}</span>
          </button>
        )
      })}
    </nav>
  )
}

// ─── PAGES ────────────────────────────────────────────────────────────────────

// LOGIN PAGE
const LoginPage = ({ onLogin, onGoRegister }) => {
  const [phone, setPhone] = useState("+237677100001")
  const [password, setPassword] = useState("Demo@12345")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showPw, setShowPw] = useState(false)

  const handleLogin = async () => {
    if (!phone || !password) return
    setLoading(true); setError(null)
    try {
      const data = await api("POST", "/auth/login", { phone, password })
      authToken = data.access_token
      localStorage.setItem("access_token", data.access_token)
      onLogin(data.user)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: "100vh", background: T.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      {/* Logo */}
      <div style={{ marginBottom: 40, textAlign: "center" }}>
        <div style={{ width: 64, height: 64, borderRadius: 18, background: `linear-gradient(135deg, ${T.gold}, ${T.goldDim})`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px", boxShadow: `0 8px 32px ${T.gold}40` }}>
          <Icon name="shield" color="#000" size={30} />
        </div>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: T.text, letterSpacing: "-0.02em" }}>CryptoBridge CM</h1>
        <p style={{ fontSize: 14, color: T.dim, marginTop: 4 }}>Échangez USDT ↔ XAF en toute sécurité</p>
      </div>

      <div style={{ width: "100%", maxWidth: 380 }}>
        <Card>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: T.text, marginBottom: 24 }}>Sign In</h2>

          {error && (
            <div style={{ background: T.redBg, border: `1px solid ${T.redBorder}`, borderRadius: 10, padding: "10px 14px", marginBottom: 16, display: "flex", gap: 8, alignItems: "center" }}>
              <Icon name="alert" color={T.red} size={16} />
              <span style={{ fontSize: 13, color: T.red }}>{error}</span>
            </div>
          )}

          <Input label="Phone Number" value={phone} onChange={setPhone} placeholder="+237677xxxxxx" prefix="📱" />
          <Input label="Password" value={password} onChange={setPassword}
            type={showPw ? "text" : "password"} placeholder="Your password"
            suffix={<button onClick={() => setShowPw(s => !s)} style={{ background: "none", border: "none", cursor: "pointer", color: T.dim, display: "flex" }}>
              <Icon name={showPw ? "eyeOff" : "eye"} size={17} />
            </button>}
          />

          <Btn onClick={handleLogin} disabled={loading} fullWidth style={{ marginTop: 8 }}>
            {loading ? <Spinner size={18} color="#000" /> : null}
            {loading ? "Signing in..." : "Sign In"}
          </Btn>

          <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: T.muted }}>
            No account?{" "}
            <button onClick={onGoRegister} style={{ background: "none", border: "none", color: T.gold, cursor: "pointer", fontWeight: 600, fontSize: 13 }}>
              Register
            </button>
          </p>
        </Card>

        {/* Demo credentials */}
        <div style={{ marginTop: 16, padding: "12px 16px", background: T.card, border: `1px solid ${T.border}`, borderRadius: 10 }}>
          <p style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Demo Accounts</p>
          {[
            { label: "Seller", phone: "+237677100001", pw: "Demo@12345" },
            { label: "Buyer", phone: "+237677100002", pw: "Demo@12345" },
          ].map(d => (
            <button key={d.label} onClick={() => { setPhone(d.phone); setPassword(d.pw) }}
              style={{ display: "block", width: "100%", textAlign: "left", background: "none", border: "none", padding: "4px 0", cursor: "pointer" }}>
              <span style={{ fontSize: 12, color: T.gold, fontWeight: 600 }}>{d.label}: </span>
              <span style={{ fontSize: 12, color: T.dim, fontFamily: T.mono }}>{d.phone}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

// REGISTER PAGE
const RegisterPage = ({ onBack, onSuccess }) => {
  const [phone, setPhone] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [lang, setLang] = useState("fr")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [step, setStep] = useState(1) // 1=form, 2=otp
  const [otp, setOtp] = useState("")
  const [otpHint, setOtpHint] = useState(null)

  const handleRegister = async () => {
    setLoading(true); setError(null)
    try {
      const data = await api("POST", "/auth/register", { phone, password, full_name: name, language: lang })
      if (data.otp_hint) setOtpHint(data.otp_hint)
      setStep(2)
    } catch (err) { setError(err.message) }
    setLoading(false)
  }

  const handleVerify = async () => {
    setLoading(true); setError(null)
    try {
      const data = await api("POST", "/auth/verify-otp", { phone, otp })
      authToken = data.access_token
      localStorage.setItem("access_token", data.access_token)
      onSuccess(data.user)
    } catch (err) { setError(err.message) }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: "100vh", background: T.bg, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: T.dim, cursor: "pointer", marginBottom: 24, display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
          ← Back to login
        </button>

        <Card>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: T.text, marginBottom: 6 }}>
            {step === 1 ? "Create Account" : "Verify Phone"}
          </h2>
          <p style={{ fontSize: 13, color: T.dim, marginBottom: 24 }}>
            {step === 1 ? "Start trading USDT safely" : `Enter the OTP sent to ${phone}`}
          </p>

          {error && (
            <div style={{ background: T.redBg, border: `1px solid ${T.redBorder}`, borderRadius: 10, padding: "10px 14px", marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: T.red }}>{error}</span>
            </div>
          )}

          {step === 1 ? (
            <>
              <Input label="Full Name" value={name} onChange={setName} placeholder="Jean Mbarga" />
              <Input label="Phone Number" value={phone} onChange={setPhone} placeholder="+237677xxxxxx" />
              <Input label="Password" value={password} onChange={setPassword} type="password" placeholder="Min. 8 characters" />
              <div style={{ marginBottom: 16 }}>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: T.dim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Language</label>
                <div style={{ display: "flex", gap: 8 }}>
                  {["fr", "en"].map(l => (
                    <button key={l} onClick={() => setLang(l)} style={{
                      flex: 1, padding: "10px", borderRadius: 10, cursor: "pointer",
                      background: lang === l ? `${T.gold}18` : T.surface,
                      border: `1px solid ${lang === l ? T.gold : T.border}`,
                      color: lang === l ? T.gold : T.dim, fontWeight: 600, fontSize: 14,
                    }}>
                      {l === "fr" ? "🇫🇷 Français" : "🇬🇧 English"}
                    </button>
                  ))}
                </div>
              </div>
              <Btn onClick={handleRegister} disabled={loading} fullWidth>
                {loading ? <Spinner size={18} color="#000" /> : "Create Account"}
              </Btn>
            </>
          ) : (
            <>
              {otpHint && (
                <div style={{ background: T.blueBg, border: `1px solid ${T.blueBorder}`, borderRadius: 10, padding: "10px 14px", marginBottom: 16 }}>
                  <p style={{ fontSize: 12, color: T.blue }}>🔧 Dev mode — OTP: <strong style={{ fontFamily: T.mono }}>{otpHint}</strong></p>
                </div>
              )}
              <Input label="6-Digit OTP Code" value={otp} onChange={setOtp} placeholder="123456"
                hint="Check your phone for the verification code" />
              <Btn onClick={handleVerify} disabled={loading} fullWidth>
                {loading ? <Spinner size={18} color="#000" /> : "Verify Phone"}
              </Btn>
            </>
          )}
        </Card>
      </div>
    </div>
  )
}

// DASHBOARD PAGE
const DashboardPage = ({ user, balance, onNavigate }) => {
  const fmt = (raw) => (raw / 1_000_000).toFixed(2)

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      {/* Greeting */}
      <div style={{ marginBottom: 24 }}>
        <p style={{ fontSize: 13, color: T.muted, marginBottom: 4 }}>
          {new Date().getHours() < 12 ? "Good morning" : "Good evening"} 👋
        </p>
        <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, letterSpacing: "-0.02em" }}>
          {user?.full_name || user?.phone}
        </h1>
        <div style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}>
          <Badge color={user?.kyc_level > 0 ? T.green : T.orange}>
            KYC Level {user?.kyc_level}
          </Badge>
          {user?.phone_verified && <Badge color={T.green}>✓ Verified</Badge>}
        </div>
      </div>

      {/* Balance */}
      <BalanceCard balance={balance}
        onDeposit={() => onNavigate("wallet")}
        onWithdraw={() => onNavigate("wallet")}
      />

      {/* Quick actions */}
      <div style={{ marginTop: 20, marginBottom: 20 }}>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Quick Actions</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {[
            { icon: "plus", label: "Sell USDT", desc: "Create a trade offer", color: T.gold, page: "create-trade" },
            { icon: "arrow", label: "Buy USDT", desc: "Join a trade", color: T.green, page: "join-trade" },
            { icon: "wallet", label: "Wallet", desc: "Manage your funds", color: T.blue, page: "wallet" },
            { icon: "shield", label: "History", desc: "View all trades", color: T.orange, page: "trades" },
          ].map(a => (
            <Card key={a.label} hover onClick={() => onNavigate(a.page)}
              style={{ padding: 16, cursor: "pointer" }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: `${a.color}15`, border: `1px solid ${a.color}25`, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 12 }}>
                <Icon name={a.icon} color={a.color} size={20} />
              </div>
              <p style={{ fontWeight: 700, fontSize: 14, color: T.text, marginBottom: 3 }}>{a.label}</p>
              <p style={{ fontSize: 12, color: T.muted }}>{a.desc}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Stats */}
      <Card>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>Your Stats</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, textAlign: "center" }}>
          {[
            { label: "Total Trades", val: user?.total_trades || 0, color: T.text },
            { label: "Completed", val: user?.completed_trades || 0, color: T.green },
            { label: "Rating", val: user?.rating_avg ? `${user.rating_avg}★` : "N/A", color: T.gold },
          ].map(s => (
            <div key={s.label}>
              <p style={{ fontSize: 22, fontWeight: 800, color: s.color, fontFamily: T.mono }}>{s.val}</p>
              <p style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>{s.label}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Security tip */}
      <div style={{ marginTop: 16, padding: "14px 16px", background: T.goldBg, border: `1px solid ${T.goldBorder}`, borderRadius: 12, display: "flex", gap: 12, alignItems: "flex-start" }}>
        <Icon name="shield" color={T.gold} size={18} />
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: T.gold, marginBottom: 3 }}>Security Reminder</p>
          <p style={{ fontSize: 12, color: T.dim, lineHeight: 1.6 }}>
            Always trade within CryptoBridge. Never share your PIN or trade on WhatsApp without escrow protection.
          </p>
        </div>
      </div>
    </div>
  )
}

// WALLET PAGE
const WalletPage = ({ balance, onRefresh }) => {
  const [depositAddress, setDepositAddress] = useState(null)
  const [mode, setMode] = useState("overview") // overview | deposit | withdraw | history
  const [txns, setTxns] = useState([])
  const [loading, setLoading] = useState(false)
  const [simAmount, setSimAmount] = useState("100")
  const [withdrawAddr, setWithdrawAddr] = useState("")
  const [copied, setCopied] = useState(false)
  const [toast, setToast] = useState(null)

  const fmt = (raw) => (raw / 1_000_000).toFixed(6)

  const loadDeposit = async () => {
    setLoading(true)
    try {
      const data = await api("GET", "/wallet/deposit-address")
      setDepositAddress(data)
    } catch {}
    setLoading(false)
  }

  const loadTxns = async () => {
    setLoading(true)
    try {
      const data = await api("GET", "/wallet/transactions")
      setTxns(data.transactions || [])
    } catch {}
    setLoading(false)
  }

  const simulateDeposit = async () => {
    setLoading(true)
    try {
      await api("POST", "/wallet/dev/simulate-deposit", { amount: parseFloat(simAmount) })
      await onRefresh()
      setToast({ msg: `${simAmount} USDT deposited (dev simulation)`, type: "success" })
      setMode("overview")
    } catch (err) { setToast({ msg: err.message, type: "error" }) }
    setLoading(false)
  }

  useEffect(() => {
    if (mode === "deposit") loadDeposit()
    if (mode === "history") loadTxns()
  }, [mode])

  const copyAddr = () => {
    if (depositAddress?.tron_address) {
      navigator.clipboard.writeText(depositAddress.tron_address)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const txTypeColor = (type, dir) => {
    if (dir === "IN") return T.green
    if (type === "TRADE_LOCK") return T.orange
    if (type === "WITHDRAWAL") return T.red
    return T.dim
  }

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      {toast && <Toast msg={toast.msg} type={toast.type} onDismiss={() => setToast(null)} />}

      <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, marginBottom: 20, letterSpacing: "-0.02em" }}>Wallet</h1>

      <BalanceCard balance={balance}
        onDeposit={() => setMode("deposit")}
        onWithdraw={() => setMode("withdraw")}
      />

      {/* Tab buttons */}
      <div style={{ display: "flex", gap: 8, marginTop: 20, marginBottom: 16 }}>
        {[
          { id: "deposit", label: "Deposit" },
          { id: "withdraw", label: "Withdraw" },
          { id: "history", label: "History" },
        ].map(t => (
          <Btn key={t.id} onClick={() => setMode(t.id)}
            variant={mode === t.id ? "primary" : "ghost"} size="sm" style={{ flex: 1 }}>
            {t.label}
          </Btn>
        ))}
      </div>

      {/* Deposit panel */}
      {mode === "deposit" && (
        <Card>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: T.text, marginBottom: 4 }}>Deposit USDT</h3>
          <p style={{ fontSize: 13, color: T.muted, marginBottom: 20 }}>Send USDT-TRC20 to your platform address</p>

          {loading ? <div style={{ textAlign: "center", padding: 20 }}><Spinner /></div> : depositAddress ? (
            <>
              <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 10, padding: 16, marginBottom: 16 }}>
                <p style={{ fontSize: 11, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 8 }}>Your TRON (TRC20) Address</p>
                <p style={{ fontFamily: T.mono, fontSize: 13, color: T.text, wordBreak: "break-all", marginBottom: 12 }}>
                  {depositAddress.tron_address}
                </p>
                <Btn onClick={copyAddr} variant="secondary" size="sm" fullWidth>
                  <Icon name={copied ? "check" : "copy"} size={15} />
                  {copied ? "Copied!" : "Copy Address"}
                </Btn>
              </div>

              {[
                { icon: "alert", text: "Send ONLY USDT-TRC20 to this address", color: T.orange },
                { icon: "check", text: "Funds arrive in ~3 seconds on TRON", color: T.green },
                { icon: "lock", text: "Minimum deposit: 1 USDT", color: T.blue },
              ].map((n, i) => (
                <div key={i} style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                  <Icon name={n.icon} color={n.color} size={15} />
                  <span style={{ fontSize: 12, color: T.dim }}>{n.text}</span>
                </div>
              ))}

              {/* Dev simulation */}
              <div style={{ marginTop: 20, padding: "14px 16px", background: T.blueBg, border: `1px solid ${T.blueBorder}`, borderRadius: 10 }}>
                <p style={{ fontSize: 12, color: T.blue, marginBottom: 10 }}>🔧 Development — Simulate Deposit</p>
                <Input label="Amount (USDT)" value={simAmount} onChange={setSimAmount} type="number" placeholder="100" />
                <Btn onClick={simulateDeposit} disabled={loading} variant="success" size="sm" fullWidth>
                  {loading ? <Spinner size={16} color={T.green} /> : "Simulate Deposit"}
                </Btn>
              </div>
            </>
          ) : null}
        </Card>
      )}

      {/* Withdraw panel */}
      {mode === "withdraw" && (
        <Card>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: T.text, marginBottom: 4 }}>Withdraw USDT</h3>
          <p style={{ fontSize: 13, color: T.muted, marginBottom: 20 }}>Send USDT to your Binance or Trust Wallet</p>

          <Input label="Destination TRON Address" value={withdrawAddr} onChange={setWithdrawAddr}
            placeholder="TXyz...abc (34 characters)" hint="Must be a TRON (TRC20) wallet address" />

          {balance && (
            <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 10, padding: 14, marginBottom: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: T.dim }}>Available</span>
                <span style={{ fontFamily: T.mono, fontSize: 13, color: T.green }}>{fmt(balance.available.raw)} USDT</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: T.dim }}>Network fee</span>
                <span style={{ fontFamily: T.mono, fontSize: 13, color: T.text }}>1 USDT (flat)</span>
              </div>
              <div style={{ borderTop: `1px solid ${T.border}`, paddingTop: 8, display: "flex", justifyContent: "space-between" }}>
                <span style={{ fontSize: 13, color: T.dim, fontWeight: 600 }}>You receive</span>
                <span style={{ fontFamily: T.mono, fontSize: 13, color: T.gold, fontWeight: 700 }}>
                  {fmt(Math.max(0, balance.available.raw - 1_000_000))} USDT
                </span>
              </div>
            </div>
          )}

          <div style={{ padding: "12px 14px", background: T.goldBg, border: `1px solid ${T.goldBorder}`, borderRadius: 10, marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: T.gold }}>💡 Fee is the same regardless of amount — TRON network is very cheap. Min withdrawal: 5 USDT.</p>
          </div>

          <Btn onClick={() => setToast({ msg: "Withdrawal available after TRON integration", type: "info" })} fullWidth>
            Withdraw USDT
          </Btn>
        </Card>
      )}

      {/* Transaction history */}
      {mode === "history" && (
        <Card style={{ padding: 0 }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: 40 }}><Spinner /></div>
          ) : txns.length === 0 ? (
            <div style={{ textAlign: "center", padding: 40 }}>
              <Icon name="trending" color={T.muted} size={40} />
              <p style={{ color: T.muted, marginTop: 12 }}>No transactions yet</p>
            </div>
          ) : txns.map((t, i) => (
            <div key={t.id} style={{
              padding: "14px 16px", borderBottom: i < txns.length - 1 ? `1px solid ${T.border}` : "none",
              display: "flex", justifyContent: "space-between", alignItems: "center",
            }}>
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, color: T.text }}>{t.type.replace(/_/g, " ")}</p>
                <p style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>
                  {new Date(t.created_at).toLocaleDateString()}
                </p>
                {t.note && <p style={{ fontSize: 11, color: T.muted }}>{t.note}</p>}
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontFamily: T.mono, fontSize: 14, fontWeight: 700, color: txTypeColor(t.type, t.direction) }}>
                  {t.direction === "IN" ? "+" : "-"}{(t.amount_usdt / 1_000_000).toFixed(2)} USDT
                </p>
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  )
}

// CREATE TRADE PAGE
const CreateTradePage = ({ onBack, onSuccess }) => {
  const [amount, setAmount] = useState("100")
  const [rate, setRate] = useState("620")
  const [method, setMethod] = useState("mtn_momo")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [trade, setTrade] = useState(null)
  const [copied, setCopied] = useState(false)

  const usdtAmt = parseFloat(amount) || 0
  const rateVal = parseInt(rate) || 0
  const xafTotal = Math.round(usdtAmt * rateVal)
  const fee = usdtAmt * 0.015
  const buyerGets = usdtAmt - fee

  const handleCreate = async () => {
    setLoading(true); setError(null)
    try {
      const data = await api("POST", "/trades/create", {
        usdt_amount: usdtAmt,
        rate_xaf_per_usdt: rateVal,
        payment_method: method,
      })
      setTrade(data.trade)
    } catch (err) { setError(err.message) }
    setLoading(false)
  }

  const copyCode = () => {
    if (trade?.trade_code) {
      navigator.clipboard.writeText(trade.trade_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (trade) return (
    <div style={{ padding: "20px 16px 100px" }}>
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <div style={{ width: 64, height: 64, borderRadius: "50%", background: `${T.green}15`, border: `1px solid ${T.green}40`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
          <Icon name="check" color={T.green} size={30} />
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: T.text }}>Trade Created!</h2>
        <p style={{ fontSize: 14, color: T.dim, marginTop: 6 }}>Share this code with your buyer on WhatsApp</p>
      </div>

      {/* Big trade code */}
      <Card style={{ textAlign: "center", padding: 28, marginBottom: 16 }}>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 12 }}>Trade Code</p>
        <p style={{ fontFamily: T.mono, fontSize: 36, fontWeight: 800, color: T.gold, letterSpacing: "0.1em" }}>
          {trade.trade_code}
        </p>
        <Btn onClick={copyCode} variant="secondary" size="sm" style={{ marginTop: 16 }}>
          <Icon name={copied ? "check" : "copy"} size={15} />
          {copied ? "Copied!" : "Copy Code"}
        </Btn>
      </Card>

      {/* Summary */}
      <Card style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>Trade Summary</p>
        {[
          { label: "You lock", val: `${usdtAmt} USDT` },
          { label: "Buyer pays", val: `${xafTotal.toLocaleString()} XAF` },
          { label: "Buyer receives", val: `${buyerGets.toFixed(4)} USDT` },
          { label: "Your fee (1.5%)", val: `${fee.toFixed(4)} USDT` },
        ].map(r => (
          <div key={r.label} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${T.border}` }}>
            <span style={{ fontSize: 13, color: T.dim }}>{r.label}</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: T.text, fontFamily: T.mono }}>{r.val}</span>
          </div>
        ))}
      </Card>

      <div style={{ padding: "12px 14px", background: T.goldBg, border: `1px solid ${T.goldBorder}`, borderRadius: 10, marginBottom: 20 }}>
        <p style={{ fontSize: 12, color: T.gold, lineHeight: 1.6 }}>
          💡 Share <strong>{trade.trade_code}</strong> with your buyer on WhatsApp. When they join, they'll receive a MoMo payment prompt automatically.
        </p>
      </div>

      <Btn onClick={onBack} variant="secondary" fullWidth>
        <Icon name="arrow" size={16} /> Back to Dashboard
      </Btn>
    </div>
  )

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      <button onClick={onBack} style={{ background: "none", border: "none", color: T.dim, cursor: "pointer", marginBottom: 20, display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
        ← Back
      </button>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, marginBottom: 6, letterSpacing: "-0.02em" }}>Sell USDT</h1>
      <p style={{ fontSize: 14, color: T.dim, marginBottom: 24 }}>Create a trade offer. USDT will be locked in escrow.</p>

      {error && (
        <div style={{ background: T.redBg, border: `1px solid ${T.redBorder}`, borderRadius: 10, padding: "12px 16px", marginBottom: 20 }}>
          <Icon name="alert" color={T.red} size={16} />
          <span style={{ fontSize: 13, color: T.red, marginLeft: 8 }}>{error}</span>
        </div>
      )}

      <Card style={{ marginBottom: 16 }}>
        <Input label="USDT Amount to Sell" value={amount} onChange={setAmount} type="number"
          placeholder="100" suffix="USDT" hint="This amount will be locked in escrow" />
        <Input label="Rate (XAF per USDT)" value={rate} onChange={setRate} type="number"
          placeholder="620" prefix="₣" hint="Market rate is typically 600–640 XAF/USDT" />

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: T.dim, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Payment Method</label>
          <div style={{ display: "flex", gap: 8 }}>
            {[
              { id: "mtn_momo", label: "📱 MTN MoMo" },
              { id: "orange_money", label: "🟠 Orange Money" },
            ].map(m => (
              <button key={m.id} onClick={() => setMethod(m.id)} style={{
                flex: 1, padding: "11px", borderRadius: 10, cursor: "pointer",
                background: method === m.id ? `${T.gold}15` : T.surface,
                border: `1px solid ${method === m.id ? T.gold : T.border}`,
                color: method === m.id ? T.gold : T.dim, fontWeight: 600, fontSize: 13,
              }}>
                {m.label}
              </button>
            ))}
          </div>
        </div>

        {/* Preview */}
        {usdtAmt > 0 && rateVal > 0 && (
          <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 10, padding: 14, marginBottom: 16 }}>
            <p style={{ fontSize: 12, color: T.muted, marginBottom: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>Trade Preview</p>
            {[
              { l: "Buyer pays", v: `${xafTotal.toLocaleString()} XAF`, c: T.text },
              { l: "Buyer receives", v: `${buyerGets.toFixed(4)} USDT`, c: T.green },
              { l: "Platform fee (1.5%)", v: `${fee.toFixed(4)} USDT`, c: T.dim },
            ].map(r => (
              <div key={r.l} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 13, color: T.dim }}>{r.l}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: r.c, fontFamily: T.mono }}>{r.v}</span>
              </div>
            ))}
          </div>
        )}

        <Btn onClick={handleCreate} disabled={loading || !usdtAmt || !rateVal} fullWidth size="lg">
          {loading ? <Spinner size={20} color="#000" /> : <Icon name="lock" size={18} />}
          {loading ? "Creating..." : "Lock USDT & Create Trade"}
        </Btn>
      </Card>

      <div style={{ padding: "12px 14px", background: T.greenBg, border: `1px solid ${T.greenBorder}`, borderRadius: 10 }}>
        <p style={{ fontSize: 12, color: T.green, lineHeight: 1.6 }}>
          🔒 Your USDT is locked in escrow immediately. The buyer cannot be scammed and you cannot lose your crypto.
        </p>
      </div>
    </div>
  )
}

// JOIN TRADE PAGE
const JoinTradePage = ({ onBack, user }) => {
  const [code, setCode] = useState("")
  const [phone, setPhone] = useState(user?.phone || "")
  const [trade, setTrade] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [simLoading, setSimLoading] = useState(false)
  const [simResult, setSimResult] = useState(null)

  const handleJoin = async () => {
    setLoading(true); setError(null)
    try {
      const data = await api("POST", "/trades/join", {
        trade_code: code.toUpperCase(),
        buyer_phone: phone,
      })
      setTrade(data.trade)
    } catch (err) { setError(err.message) }
    setLoading(false)
  }

  const handleSimPay = async () => {
    if (!trade) return
    setSimLoading(true)
    try {
      const data = await api("POST", `/trades/${trade.id}/dev/simulate-payment`)
      setSimResult(data)
      setTrade(data.trade)
    } catch (err) { setError(err.message) }
    setSimLoading(false)
  }

  const fmt = v => (v / 1_000_000).toFixed(4)

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      <button onClick={onBack} style={{ background: "none", border: "none", color: T.dim, cursor: "pointer", marginBottom: 20, display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
        ← Back
      </button>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, marginBottom: 6, letterSpacing: "-0.02em" }}>Buy USDT</h1>
      <p style={{ fontSize: 14, color: T.dim, marginBottom: 24 }}>Enter the trade code shared by the seller</p>

      {error && (
        <div style={{ background: T.redBg, border: `1px solid ${T.redBorder}`, borderRadius: 10, padding: "12px 16px", marginBottom: 16 }}>
          <span style={{ fontSize: 13, color: T.red }}>{error}</span>
        </div>
      )}

      {!trade ? (
        <Card>
          <Input label="Trade Code" value={code} onChange={setCode}
            placeholder="TRD-123456" hint="Get this code from the seller on WhatsApp" />
          <Input label="Your MTN MoMo Number" value={phone} onChange={setPhone}
            placeholder="+237677xxxxxx" hint="The MoMo payment request will be sent to this number" />
          <Btn onClick={handleJoin} disabled={loading || !code || !phone} fullWidth size="lg">
            {loading ? <Spinner size={20} color="#000" /> : null}
            {loading ? "Joining..." : "Join Trade & Pay"}
          </Btn>
        </Card>
      ) : (
        <>
          {/* Trade info */}
          <Card style={{ marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: T.text }}>{trade.trade_code}</h3>
              <StatusBadge status={trade.status} />
            </div>

            {[
              { l: "You pay", v: `${(trade.xaf_amount || 0).toLocaleString()} XAF`, c: T.orange },
              { l: "You receive", v: `${fmt(trade.usdt_buyer_receives)} USDT`, c: T.green },
              { l: "Rate", v: `${trade.rate_xaf_per_usdt} XAF/USDT`, c: T.text },
            ].map(r => (
              <div key={r.l} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${T.border}` }}>
                <span style={{ fontSize: 13, color: T.dim }}>{r.l}</span>
                <span style={{ fontSize: 14, fontWeight: 700, color: r.c, fontFamily: T.mono }}>{r.v}</span>
              </div>
            ))}
          </Card>

          {/* Payment status */}
          {trade.status === "PAYMENT_PENDING" && (
            <Card style={{ textAlign: "center", marginBottom: 16 }}>
              <div style={{ marginBottom: 20 }}>
                <Icon name="alert" color={T.orange} size={36} />
                <h3 style={{ fontSize: 16, fontWeight: 700, color: T.text, marginTop: 12 }}>Approve MoMo Payment</h3>
                <p style={{ fontSize: 13, color: T.dim, marginTop: 6 }}>
                  A payment request of <strong style={{ color: T.text }}>{(trade.xaf_amount || 0).toLocaleString()} XAF</strong> has been sent to {trade.buyer_phone}
                </p>
              </div>
              {trade.payment_deadline && <Countdown deadline={trade.payment_deadline} />}

              {/* Dev simulation */}
              <div style={{ marginTop: 20, padding: "14px 16px", background: T.blueBg, border: `1px solid ${T.blueBorder}`, borderRadius: 10 }}>
                <p style={{ fontSize: 12, color: T.blue, marginBottom: 10 }}>🔧 Dev: Simulate MTN MoMo Confirmation</p>
                <Btn onClick={handleSimPay} disabled={simLoading} variant="success" fullWidth size="sm">
                  {simLoading ? <Spinner size={16} color={T.green} /> : "Simulate Payment Approved ✓"}
                </Btn>
              </div>
            </Card>
          )}

          {/* Completed */}
          {(trade.status === "COMPLETED" || trade.status === "PAID") && simResult && (
            <Card style={{ textAlign: "center", background: T.greenBg, border: `1px solid ${T.greenBorder}` }}>
              <div style={{ width: 56, height: 56, borderRadius: "50%", background: `${T.green}20`, display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
                <Icon name="check" color={T.green} size={26} />
              </div>
              <h3 style={{ fontSize: 18, fontWeight: 800, color: T.green }}>Payment Confirmed!</h3>
              <p style={{ fontSize: 13, color: T.dim, marginTop: 8, marginBottom: 16 }}>
                {fmt(simResult.buyer_credited)} USDT has been credited to your wallet
                {simResult.hold_minutes > 0 ? ` (on hold for ${simResult.hold_minutes} minutes)` : " (available now)"}
              </p>
              {trade.tron_tx_hash && (
                <Badge color={T.green}>TX: {trade.tron_tx_hash}</Badge>
              )}
            </Card>
          )}
        </>
      )}
    </div>
  )
}

// TRADES LIST PAGE
const TradesPage = ({ user }) => {
  const [trades, setTrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState("all")

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const data = await api("GET", `/trades/my/list?role=${filter}`)
        setTrades(data.trades || [])
      } catch {}
      setLoading(false)
    }
    load()
  }, [filter])

  const fmt = v => (v / 1_000_000).toFixed(2)

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, marginBottom: 20, letterSpacing: "-0.02em" }}>Trade History</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["all", "seller", "buyer"].map(f => (
          <Btn key={f} onClick={() => setFilter(f)} variant={filter === f ? "primary" : "ghost"} size="sm" style={{ flex: 1, textTransform: "capitalize" }}>
            {f}
          </Btn>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 60 }}><Spinner size={36} /></div>
      ) : trades.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60 }}>
          <Icon name="trade" color={T.muted} size={48} />
          <p style={{ color: T.muted, marginTop: 16, fontSize: 15 }}>No trades yet</p>
          <p style={{ color: T.muted, fontSize: 13, marginTop: 6 }}>Create or join a trade to get started</p>
        </div>
      ) : (
        trades.map(trade => {
          const isSeller = trade.seller?.id === user?.id
          return (
            <Card key={trade.id} hover style={{ marginBottom: 10 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div>
                  <p style={{ fontFamily: T.mono, fontSize: 14, fontWeight: 700, color: T.gold }}>{trade.trade_code}</p>
                  <p style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>
                    {isSeller ? "You sold" : "You bought"} • {new Date(trade.created_at).toLocaleDateString()}
                  </p>
                </div>
                <StatusBadge status={trade.status} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                  <p style={{ fontSize: 12, color: T.muted }}>USDT</p>
                  <p style={{ fontFamily: T.mono, fontSize: 16, fontWeight: 700, color: T.text }}>
                    {fmt(trade.usdt_amount)}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 12, color: T.muted }}>XAF</p>
                  <p style={{ fontFamily: T.mono, fontSize: 16, fontWeight: 700, color: T.text }}>
                    {(trade.xaf_amount || 0).toLocaleString()}
                  </p>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p style={{ fontSize: 12, color: T.muted }}>Rate</p>
                  <p style={{ fontFamily: T.mono, fontSize: 14, fontWeight: 700, color: T.dim }}>
                    {trade.rate_xaf_per_usdt} XAF
                  </p>
                </div>
              </div>
            </Card>
          )
        })
      )}
    </div>
  )
}

// PROFILE PAGE
const ProfilePage = ({ user, onLogout }) => {
  const kycLabels = ["Phone Only", "Phone Verified", "ID Submitted", "Fully Verified"]
  const kycColors = [T.red, T.orange, T.blue, T.green]

  return (
    <div style={{ padding: "20px 16px 100px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, color: T.text, marginBottom: 24, letterSpacing: "-0.02em" }}>Profile</h1>

      {/* Avatar */}
      <Card style={{ textAlign: "center", padding: 28, marginBottom: 16 }}>
        <div style={{
          width: 72, height: 72, borderRadius: "50%", background: `linear-gradient(135deg, ${T.gold}, ${T.goldDim})`,
          display: "flex", alignItems: "center", justifyContent: "center",
          margin: "0 auto 16px", fontSize: 28, fontWeight: 800, color: "#000",
        }}>
          {(user?.full_name || user?.phone || "?")[0].toUpperCase()}
        </div>
        <h2 style={{ fontSize: 18, fontWeight: 800, color: T.text }}>{user?.full_name || "User"}</h2>
        <p style={{ fontSize: 13, color: T.dim, marginTop: 4, fontFamily: T.mono }}>{user?.phone}</p>
        <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 12 }}>
          <Badge color={kycColors[user?.kyc_level || 0]}>
            KYC {user?.kyc_level}: {kycLabels[user?.kyc_level || 0]}
          </Badge>
          {user?.is_admin && <Badge color={T.purple}>Admin</Badge>}
        </div>
      </Card>

      {/* Stats */}
      <Card style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 14 }}>Trading Stats</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {[
            { label: "Total Trades", val: user?.total_trades || 0, color: T.text },
            { label: "Completed", val: user?.completed_trades || 0, color: T.green },
            { label: "Cancelled", val: user?.cancelled_trades || 0, color: T.red },
            { label: "Strikes", val: user?.strike_count || 0, color: user?.strike_count > 0 ? T.orange : T.muted },
          ].map(s => (
            <div key={s.label} style={{ background: T.surface, borderRadius: 10, padding: "12px 14px" }}>
              <p style={{ fontSize: 22, fontWeight: 800, color: s.color, fontFamily: T.mono }}>{s.val}</p>
              <p style={{ fontSize: 11, color: T.muted, marginTop: 2 }}>{s.label}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* KYC upgrade */}
      {user?.kyc_level < 3 && (
        <Card style={{ marginBottom: 16, background: T.goldBg, border: `1px solid ${T.goldBorder}` }}>
          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <Icon name="trending" color={T.gold} size={20} />
            <div>
              <p style={{ fontSize: 14, fontWeight: 700, color: T.gold, marginBottom: 6 }}>Upgrade Your KYC</p>
              <p style={{ fontSize: 13, color: T.dim, lineHeight: 1.6, marginBottom: 12 }}>
                Increase your trade limits and reduce hold times by verifying your identity.
              </p>
              <Btn size="sm">Upload ID Documents</Btn>
            </div>
          </div>
        </Card>
      )}

      {/* Language */}
      <Card style={{ marginBottom: 16 }}>
        <p style={{ fontSize: 12, color: T.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 12 }}>Language</p>
        <div style={{ display: "flex", gap: 8 }}>
          {["fr", "en"].map(l => (
            <div key={l} style={{
              flex: 1, padding: "10px", borderRadius: 10, textAlign: "center",
              background: user?.language === l ? `${T.gold}15` : T.surface,
              border: `1px solid ${user?.language === l ? T.gold : T.border}`,
              color: user?.language === l ? T.gold : T.dim, fontWeight: 600, fontSize: 13,
            }}>
              {l === "fr" ? "🇫🇷 Français" : "🇬🇧 English"}
            </div>
          ))}
        </div>
      </Card>

      <Btn onClick={onLogout} variant="danger" fullWidth>
        <Icon name="logout" size={18} /> Sign Out
      </Btn>
    </div>
  )
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function CryptoBridgeCM() {
  const [auth, setAuth] = useState({ user: null, loading: true })
  const [balance, setBalance] = useState(null)
  const [page, setPage] = useState("dashboard")
  const [view, setView] = useState(null) // sub-pages
  const [toasts, setToasts] = useState([])

  const addToast = (msg, type = "success") => {
    const id = Date.now()
    setToasts(t => [...t, { id, msg, type }])
  }

  // Init: check stored token
  useEffect(() => {
    const token = localStorage.getItem("access_token")
    if (!token) { setAuth({ user: null, loading: false }); return }
    authToken = token
    api("GET", "/auth/me")
      .then(user => setAuth({ user, loading: false }))
      .catch(() => { localStorage.clear(); setAuth({ user: null, loading: false }) })
  }, [])

  const loadBalance = useCallback(async () => {
    try {
      const data = await api("GET", "/wallet/balance")
      setBalance(data)
    } catch {}
  }, [])

  useEffect(() => {
    if (auth.user) loadBalance()
  }, [auth.user])

  const handleLogin = (user) => setAuth({ user, loading: false })
  const handleLogout = () => {
    localStorage.clear()
    authToken = null
    setAuth({ user: null, loading: false })
    setBalance(null)
    setPage("dashboard")
    setView(null)
  }

  if (auth.loading) return (
    <div style={{ minHeight: "100vh", background: T.bg, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center" }}>
        <Spinner size={48} />
        <p style={{ color: T.dim, marginTop: 16, fontSize: 14 }}>Loading CryptoBridge...</p>
      </div>
    </div>
  )

  if (!auth.user) {
    if (view === "register") return (
      <div style={{ fontFamily: T.sans, background: T.bg }}>
        <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes spin { to { transform: rotate(360deg); } } @keyframes slideUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } } @keyframes pulse { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } } input::placeholder { color: #4a5268; } body { background: ${T.bg}; }`}</style>
        <RegisterPage
          onBack={() => setView(null)}
          onSuccess={handleLogin}
        />
      </div>
    )
    return (
      <div style={{ fontFamily: T.sans, background: T.bg }}>
        <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes spin { to { transform: rotate(360deg); } } @keyframes slideUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } } input::placeholder { color: #4a5268; } body { background: ${T.bg}; }`}</style>
        <LoginPage onLogin={handleLogin} onGoRegister={() => setView("register")} />
      </div>
    )
  }

  // Sub-pages (not in bottom nav)
  if (view === "create-trade") return (
    <div style={{ fontFamily: T.sans, background: T.bg, minHeight: "100vh" }}>
      <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes spin { to { transform: rotate(360deg); } } input::placeholder { color: #4a5268; } body { background: ${T.bg}; }`}</style>
      <CreateTradePage
        onBack={() => { setView(null); setPage("dashboard"); loadBalance() }}
        onSuccess={() => { setView(null); setPage("dashboard"); loadBalance() }}
      />
      <ChatWidget language={auth.user?.language || "fr"} />
    </div>
  )

  if (view === "join-trade") return (
    <div style={{ fontFamily: T.sans, background: T.bg, minHeight: "100vh" }}>
      <style>{`* { box-sizing: border-box; margin: 0; padding: 0; } @keyframes spin { to { transform: rotate(360deg); } } @keyframes pulse { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } } input::placeholder { color: #4a5268; } body { background: ${T.bg}; }`}</style>
      <JoinTradePage
        onBack={() => { setView(null); setPage("dashboard"); loadBalance() }}
        user={auth.user}
      />
      <ChatWidget language={auth.user?.language || "fr"} />
    </div>
  )

  const navigate = (dest) => {
    if (dest === "create-trade" || dest === "join-trade") { setView(dest); return }
    setPage(dest)
    setView(null)
  }

  return (
    <div style={{ fontFamily: T.sans, background: T.bg, minHeight: "100vh", maxWidth: 480, margin: "0 auto" }}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes slideUp { from { opacity: 0; transform: translateX(-50%) translateY(10px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
        @keyframes pulse { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } }
        input::placeholder { color: #4a5268; }
        body { background: ${T.bg}; }
        ::-webkit-scrollbar { width: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${T.border}; border-radius: 2px; }
      `}</style>

      {toasts.map(t => <Toast key={t.id} msg={t.msg} type={t.type} onDismiss={() => setToasts(ts => ts.filter(x => x.id !== t.id))} />)}

      {page === "dashboard" && <DashboardPage user={auth.user} balance={balance} onNavigate={navigate} />}
      {page === "wallet" && <WalletPage balance={balance} onRefresh={loadBalance} />}
      {page === "trades" && <TradesPage user={auth.user} />}
      {page === "profile" && <ProfilePage user={auth.user} onLogout={handleLogout} />}

      <BottomNav page={page} setPage={(p) => { setPage(p); setView(null) }} />
      <ChatWidget language={auth.user?.language || "fr"} />
    </div>
  )
}
