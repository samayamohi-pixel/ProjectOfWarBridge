import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'

type IconName = 'home' | 'shield' | 'people' | 'bolt' | 'arrow' | 'bell' | 'chevron' | 'requests' | 'phone' | 'star' | 'report' | 'settings' | 'check' | 'clock' | 'bed' | 'medical' | 'alert' | 'megaphone' | 'user' | 'close' | 'search' | 'pin' | 'heart' | 'logout'
const paths: Record<IconName, ReactNode> = {
  home: <><path d="m3 11 9-8 9 8"/><path d="M5 10v11h5v-7h4v7h5V10"/></>,
  shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/></>,
  people: <><circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M17 4a3 3 0 0 1 0 6m1 4a5 5 0 0 1 3 5v2"/></>,
  bolt: <path d="m13 2-9 12h7l-1 8 10-13h-8z"/>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6"/>,
  bell: <><path d="M5 17h14l-2-4V8a5 5 0 0 0-10 0v5zM10 21h4"/><path d="M12 2v1"/></>,
  chevron: <path d="m8 10 4 4 4-4"/>,
  requests: <><path d="M9 5H5v16h14V5h-4M9 3h6v5H9zM8 12h8M8 16h6"/></>,
  phone: <path d="m5 3 4 1 1 5-3 2a15 15 0 0 0 6 6l2-3 5 1 1 4c-1 6-9 1-13-3S0 4 5 3Z"/>,
  star: <path d="m12 2 3 6.5 7 1-5 5 1.2 7-6.2-3.3-6.2 3.3 1.2-7-5-5 7-1z"/>,
  report: <><rect x="5" y="5" width="14" height="15" rx="2"/><path d="M9 2v6m6-6v6m-3 3v3m0 3v.1"/></>,
  settings: <><path d="m9 3-1 3-3 1-2 4 2 2v4l4 2 2 2 4-1 1-3 3-1 2-4-2-2V6l-4-2-2-2z"/><circle cx="12" cy="12" r="3"/></>,
  check: <path d="m5 12 4 4L19 6"/>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/></>,
  bed: <><path d="M3 4v17m18-10v10M3 17h18M3 8h7v7H3m7-4h8a3 3 0 0 1 3 3v3"/></>,
  medical: <path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z"/>,
  alert: <><path d="m12 3 10 18H2z"/><path d="M12 9v5m0 3v.2"/></>,
  megaphone: <><path d="m3 9 15-5v16L3 15zm15 0h3v6h-3M6 16l2 6h4l-2-5"/></>,
  user: <><circle cx="12" cy="7" r="4"/><path d="M4 22v-3a8 8 0 0 1 16 0v3"/></>,
  close: <path d="m6 6 12 12M6 18 18 6"/>,
  search: <><circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/></>,
  pin: <><path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/></>,
  heart: <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>,
  logout: <><path d="M9 3H3v18h6m5-14 5 5-5 5m-6-5h13"/></>,
}
function Icon({ name, size = 18, className = '' }: { name: IconName; size?: number; className?: string }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">{paths[name]}</svg>
}
function Logo() {
  return <span className="logo"><svg width="35" height="33" viewBox="0 0 40 38" fill="none" aria-hidden="true"><path d="M20 32 5 18C-5 6 13-3 20 10 27-3 45 6 35 18Z" stroke="currentColor" strokeWidth="3.5" strokeLinejoin="round"/><path d="m4 23 8-9 8 9 8-9 8 9M13 28l7-6 7 6" stroke="currentColor" strokeWidth="3.5" strokeLinejoin="round"/></svg><span>WarBridge</span></span>
}
type Modal = 'shelters' | 'services' | 'alerts' | 'about' | 'signin' | 'sos' | 'requests' | 'helplines' | 'ratings' | 'reports' | 'settings' | 'donate' | 'verification' | 'audit' | 'request-detail' | null
type View = 'home' | 'displaced' | 'ngo' | 'admin'
const views: { id: View; label: string }[] = [
  { id: 'home', label: 'Find Help' },
  { id: 'displaced', label: 'My Support' },
  { id: 'ngo', label: 'Partner Hub' },
  { id: 'admin', label: 'Trust & Safety' },
]
type RequestItem = { id: number; title: string; city: string; time: string; icon: IconName; accepted: boolean; urgent?: boolean }
const initialRequests: RequestItem[] = [
  { id: 1, title: 'Emergency Help Needed', city: 'Bengaluru, KA', time: '5 mins ago', icon: 'alert', urgent: true, accepted: false },
  { id: 2, title: 'Room Request', city: 'Mysuru, KA', time: '12 mins ago', icon: 'bed', accepted: false },
  { id: 3, title: 'Medical Assistance', city: 'Bengaluru, KA', time: '20 mins ago', icon: 'medical', accepted: false },
]
const initialVerifications = [
  { id: 1, name: 'Hope Foundation', role: 'NGO', time: '2h' },
  { id: 2, name: 'Safe Stay Home', role: 'Host', time: '3h' },
  { id: 3, name: 'Helping Hands NGO', role: 'NGO', time: '5h' },
]
const shelters = [
  { name: 'Hope Community Shelter', city: 'Bengaluru', beds: 12, women: true, rating: '4.8', area: 'Indiranagar' },
  { name: 'Safe Haven Family Centre', city: 'Bengaluru', beds: 8, women: false, rating: '4.9', area: 'Whitefield' },
  { name: 'New Beginnings Shelter', city: 'Mysuru', beds: 6, women: true, rating: '4.7', area: 'Gokulam' },
]

export default function App() {
  const [view, setView] = useState<View>('home')
  const [modal, setModal] = useState<Modal>(null)
  const [toast, setToast] = useState('')
  const [requests, setRequests] = useState(initialRequests)
  const [verifications, setVerifications] = useState(initialVerifications)
  const [adminTab, setAdminTab] = useState('Pending Verifications')
  const [alertText, setAlertText] = useState('')
  const [alerts, setAlerts] = useState(['Shelter beds available at Hope Community Shelter', 'Fresh meals available in Indiranagar until 8 PM'])
  const [city, setCity] = useState('')
  const [womenOnly, setWomenOnly] = useState(false)
  const [requested, setRequested] = useState<string[]>([])
  const [selectedRequest, setSelectedRequest] = useState<RequestItem | null>(null)
  const [selectedOrg, setSelectedOrg] = useState('Hope Foundation')
  const [rating, setRating] = useState(0)
  const [period, setPeriod] = useState('7d')
  const [reportBlocked, setReportBlocked] = useState(false)
  const [reportDismissed, setReportDismissed] = useState(false)
  const modalRef = useRef<HTMLElement>(null)
  useEffect(() => {
    if (!modal) return
    const previousFocus = document.activeElement as HTMLElement | null
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    modalRef.current?.focus()
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setModal(null)
      if (event.key !== 'Tab') return
      const controls = modalRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href], input, textarea, select')
      if (!controls?.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && (document.activeElement === first || document.activeElement === modalRef.current)) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleKey)
    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleKey)
      previousFocus?.focus()
    }
  }, [modal])
  const notify = (message: string) => { setToast(message); window.setTimeout(() => setToast(''), 4500) }
  const open = (value: Modal) => setModal(value)
  const accept = (id: number) => { setRequests(items => items.map(r => r.id === id ? { ...r, accepted: true } : r)); notify('Demo request accepted. No real requester was contacted.') }
  const decide = (id: number, approved: boolean) => { const org = verifications.find(v => v.id === id); setVerifications(items => items.filter(v => v.id !== id)); notify(`${org?.name} ${approved ? 'approved' : 'rejected'} in this demo.`) }
  const postAlert = (event: FormEvent) => { event.preventDefault(); if (!alertText.trim()) return; setAlerts(items => [alertText.trim(), ...items]); setAlertText(''); notify('Demo alert published. View it on the public Alerts page.') }
  const navAction = (label: string) => {
    const map: Record<string, Modal> = { 'My Requests': 'requests', 'Help Requests': 'requests', 'Safety Helplines': 'helplines', Ratings: 'ratings', Reports: 'reports', Settings: 'settings', Shelters: 'shelters', Services: 'services', Alerts: 'alerts', Verification: 'verification', 'Audit Log': 'audit' }
    if (label !== 'Dashboard') open(map[label] || 'about')
  }
  function Sidebar({ role, items, active = 'Dashboard' }: { role: 'user' | 'ngo' | 'admin'; items: [IconName, string][]; active?: string }) {
    return <aside className="sidebar"><Logo /><nav aria-label={`${role} navigation`}>{items.map(([icon, label]) => <button key={label} className={`side-link ${label === active ? 'active' : ''}`} onClick={() => navAction(label)}><Icon name={icon} /><span>{label}</span></button>)}</nav><div className="sidebar-status"><span className="status-check"><Icon name="check" size={13}/></span><div><strong>{role === 'ngo' ? 'NGO Verified' : role === 'admin' ? 'System Status' : 'Verified User'}</strong><small>{role === 'ngo' ? 'Trusted Partner' : role === 'admin' ? 'All systems operational' : 'Stay Safe Together'}</small></div></div></aside>
  }
  function Profile({ name, initial }: { name: string; initial: string }) {
    return <button className="profile" onClick={() => open('settings')}><span className="avatar">{initial}</span><span>{name}</span><Icon name="chevron" size={12}/></button>
  }
  function Helplines({ full = false }: { full?: boolean }) {
    return <div className={`helpline-list ${full ? 'full' : ''}`}>{([{ name: 'Women Helpline', number: '181', icon: 'phone' }, { name: 'Emergency Response', number: '112', icon: 'phone' }, { name: 'Child Helpline', number: '1098', icon: 'shield' }] as { name: string; number: string; icon: IconName }[]).map(item => <a key={item.number} href={`tel:${item.number}`}><span className="helpline-icon"><Icon name={item.icon} size={22}/></span><span>{item.name}<strong>{item.number}</strong></span></a>)}</div>
  }

  return <div className="app-shell">
    <header className="view-header"><nav className="view-navigation" aria-label="WarBridge pages">{views.map(item => <button key={item.id} aria-pressed={view === item.id} className={view === item.id ? 'current-view' : ''} onClick={() => setView(item.id)}>{item.label}</button>)}</nav><span className="preview-label"><span className="live-dot"/> Interactive preview</span></header>
    <main className="showcase page-layout">
    <section className="panel landing purple" hidden={view !== 'home'} aria-label="WarBridge public home">
      <div className="landing-image" /><div className="orbital orbital-one"/><div className="orbital orbital-two"/>
      <header className="landing-nav"><Logo/><nav aria-label="Public navigation"><button onClick={() => open('shelters')}>Shelters</button><button onClick={() => open('services')}>Services</button><button onClick={() => open('alerts')}>Alerts</button><button onClick={() => open('about')}>About</button></nav><button className="sign-in" onClick={() => open('signin')}>Sign In</button></header>
      <div className="hero-copy"><div className="eyebrow"><span/> A bridge to a safer tomorrow</div><h1>War<span>Bridge</span></h1><h2>Find help. <span>Stay safe.</span></h2><p>Verified shelters, food, healthcare and more —<br className="desktop-break"/> for people in need.</p><div className="hero-actions"><button className="primary purple-button" onClick={() => open('shelters')}>Find Shelters <Icon name="arrow" size={17}/></button><button className="sos-button" onClick={() => open('sos')}><Icon name="alert" size={22}/> Emergency SOS</button></div><div className="trust-row"><div><span className="trust-icon"><Icon name="shield" size={24}/></span><span>Verified<br/>Shelters</span></div><div><span className="trust-icon"><Icon name="people" size={24}/></span><span>Trusted<br/>NGOs & Hosts</span></div><div><span className="trust-icon"><Icon name="bolt" size={24}/></span><span>Real-Time<br/>Alerts</span></div></div></div>
      <span className="landing-footnote"><span className="live-dot"/> Human connection. Real hope.</span>
    </section>

    <section className="panel dashboard green" hidden={view !== 'displaced'} aria-label="Displaced user dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="user" items={[['home', 'Dashboard'], ['requests', 'My Requests'], ['phone', 'Safety Helplines'], ['star', 'Ratings'], ['report', 'Reports'], ['settings', 'Settings']]}/>
      <div className="dashboard-main user-main">
        <div className="topbar"><span className="workspace-label">YOUR SAFE SPACE</span><div className="topbar-right"><button className="notification" aria-label="View notifications" onClick={() => open('alerts')}><Icon name="bell"/><span>{alerts.length}</span></button><Profile name="User" initial="U"/></div></div>
        <div className="welcome"><div><h2>Welcome back!</h2><p>You’re not alone. Help is here.</p></div><span className="verified-badge"><Icon name="shield" size={16}/> Verified User</span></div>
        <div className="stats-grid"><div className="stat"><span className="stat-icon"><Icon name="home" size={31}/></span><div><strong>{2 + requested.length}</strong><small>Active Requests</small></div></div><div className="stat"><span className="stat-icon gold"><Icon name="star" size={30}/></span><div><strong>4.6</strong><small>Your Rating</small></div></div><div className="stat"><span className="stat-icon"><Icon name="people" size={31}/></span><div><strong>3</strong><small>Reports Filed</small></div></div></div>
        <div className="user-middle"><div className="surface help-progress"><div className="section-heading"><h3>Your Help Requests</h3><button className="text-link" onClick={() => open('requests')}>View all <Icon name="arrow" size={13}/></button></div><div className="steps"><div className="step done"><span><Icon name="check" size={13}/></span><strong>Request Sent</strong><small>21 Nov, 10:24 AM</small></div><div className="step done"><span><Icon name="check" size={13}/></span><strong>Accepted</strong><small>21 Nov, 12:10 PM</small></div><div className="step"><span><Icon name="clock" size={16}/></span><strong>Completed</strong><small>—</small></div></div><div className="success-note"><span className="status-check"><Icon name="check" size={12}/></span><p>Your request has been accepted by an NGO.<br/><span>You’ll be notified once the host confirms the details.</span></p></div></div><div className="surface helplines-card"><h3>Safety Helplines</h3><Helplines/><button className="text-link helplines-more" onClick={() => open('helplines')}>View More <Icon name="arrow" size={11}/></button></div></div>
        <div className="impact-banner"><div className="banner-art"><Icon name="heart" size={64}/></div><div><h3>Together, we can rebuild.</h3><p>Support. Shelter. Hope.</p></div><button className="primary" onClick={() => open('donate')}>Get involved <Icon name="arrow" size={13}/></button></div>
      </div>
    </section>

    <section className="panel dashboard red" hidden={view !== 'ngo'} aria-label="NGO dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="ngo" items={[['home', 'Dashboard'], ['home', 'Help Requests'], ['bed', 'Shelters'], ['medical', 'Services'], ['megaphone', 'Alerts'], ['report', 'Reports'], ['settings', 'Settings']]}/>
      <div className="dashboard-main ngo-main"><div className="topbar"><span className="workspace-label">PARTNER WORKSPACE</span><Profile name="Hope Foundation" initial="H"/></div><div className="welcome"><div><h2>NGO Dashboard</h2><p>Provide help. Make a difference.</p></div></div>
        <div className="stats-grid ngo-stats"><div className="stat"><span className="stat-icon violet"><Icon name="home" size={31}/></span><div><strong>12</strong><small>Shelters Listed</small></div></div><div className="stat"><span className="stat-icon lime"><Icon name="people" size={31}/></span><div><strong>247</strong><small>People Assisted</small></div></div><div className="stat"><span className="stat-icon danger"><Icon name="alert" size={31}/></span><div><strong>{requests.filter(r => !r.accepted).length}</strong><small>Emergency Requests</small></div></div></div>
        <div className="ngo-middle"><div className="surface incoming"><div className="section-heading"><h3>Incoming Help Requests</h3><button className="text-link" onClick={() => open('requests')}>View all <Icon name="arrow" size={12}/></button></div><div className="request-list">{requests.map(request => <div className="request-row" key={request.id}><span className={`request-icon ${request.urgent ? 'urgent' : ''}`}>{request.urgent ? 'SOS' : <Icon name={request.icon} size={28}/>}</span><div className="request-info"><strong>{request.title}{request.urgent && <i/>}</strong><small>{request.city} · {request.time}</small></div><button className="outline-button" onClick={() => { setSelectedRequest(request); open('request-detail') }}>View</button><button className={`accept-button ${request.accepted ? 'accepted' : ''}`} disabled={request.accepted} onClick={() => accept(request.id)}>{request.accepted ? 'Accepted' : 'Accept'}</button></div>)}</div></div><form className="surface post-alert" onSubmit={postAlert}><h3>Post an Alert</h3><div className="alert-hint"><Icon name="megaphone" size={23}/><p>Share important updates<br/>with the community.</p></div><label className="sr-only" htmlFor="alert-message">Alert message</label><textarea id="alert-message" required maxLength={300} value={alertText} onChange={event => setAlertText(event.target.value)} placeholder="Type your message..."/><button className="accept-button" type="submit">Post Alert</button></form></div>
        <div className="impact-banner ngo-banner"><div className="banner-art"><Icon name="people" size={64}/></div><div><h3>Be the bridge in someone’s journey.</h3><p>Your support makes a difference.</p></div><button className="outline-button" onClick={() => open('about')}>Learn More <Icon name="arrow" size={12}/></button></div>
      </div>
    </section>

    <section className="panel dashboard blue" hidden={view !== 'admin'} aria-label="Admin dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="admin" active="Verification" items={[['home', 'Dashboard'], ['shield', 'Verification'], ['report', 'Reports'], ['requests', 'Audit Log'], ['settings', 'Settings']]}/>
      <div className="dashboard-main admin-main"><div className="topbar"><span className="workspace-label">TRUST & SAFETY</span><Profile name="Admin" initial="A"/></div><div className="welcome"><div><h2>Admin Panel</h2><p>Verify. Monitor. Ensure Safety.</p></div><Icon name="shield" size={85} className="admin-shield"/></div>
        <div className="admin-middle"><div className="verification-section"><div className="tabs" role="tablist" aria-label="Admin lists">{['Pending Verifications', 'Reports', 'Blocked Listings'].map((tab, i) => <button key={tab} role="tab" aria-selected={adminTab === tab} onClick={() => setAdminTab(tab)} className={adminTab === tab ? 'selected' : ''}>{tab} ({i === 0 ? verifications.length : i === 1 ? (reportBlocked || reportDismissed ? 2 : 3) : reportBlocked ? 2 : 1})</button>)}</div><div className="surface verification-list">{adminTab === 'Pending Verifications' ? verifications.length ? verifications.map(org => <div className="verification-row" key={org.id}><span className="org-icon"><Icon name="user" size={27}/></span><div className="org-info"><strong>{org.name}</strong><small>{org.role} · Registered {org.time} ago</small></div><button className="outline-button" onClick={() => { setSelectedOrg(org.name); open('verification') }}>View</button><button className="approve-button" onClick={() => decide(org.id, true)}>Approve</button><button className="reject-button" onClick={() => decide(org.id, false)}>Reject</button></div>) : <div className="empty-state"><Icon name="check" size={30}/><p>All verifications reviewed.</p></div> : adminTab === 'Reports' ? <div className="admin-report"><Icon name="alert"/><strong>{reportBlocked ? 'Listing blocked' : reportDismissed ? 'Report dismissed' : 'Fake Shelter Listing'}</strong><p>Reported for an unverified address and suspicious contact details.</p>{!reportBlocked && !reportDismissed && <div className="button-row"><button className="reject-button" onClick={() => { setReportBlocked(true); notify('Demo listing blocked and related report closed.') }}>Block listing</button><button className="outline-button" onClick={() => { setReportDismissed(true); notify('Demo report dismissed.') }}>Dismiss</button></div>}</div> : <div className="admin-report"><Icon name="shield"/><strong>{reportBlocked ? '2 listings blocked' : '1 listing blocked'}</strong><p>Unsafe listings are hidden from public search.</p><button className="outline-button" onClick={() => { setReportBlocked(false); notify('Demo listing unblocked.') }}>Review & unblock</button></div>}</div></div><div className="surface activity"><div className="section-heading"><h3>Recent Activity</h3><button className="text-link" onClick={() => open('audit')}>View all <Icon name="arrow" size={11}/></button></div><div className="activity-item"><i className="activity-dot mint"/><p>New NGO verified:<br/>Helping Hands NGO<small>2m ago</small></p></div><div className="activity-item"><i className="activity-dot pink"/><p>Suspicious report:<br/>Fake Shelter Listing<small>8m ago</small></p></div><div className="activity-item"><i className="activity-dot amber"/><p>New alert posted<small>12m ago</small></p></div></div></div>
        <div className="surface chart-card"><div className="section-heading"><h3>Platform Overview</h3><select aria-label="Chart period" value={period} onChange={event => setPeriod(event.target.value)}><option value="7d">7d</option><option value="30d">30d</option></select></div><div className="chart-body"><div className="chart-scale"><span>{period === '7d' ? 100 : 500}</span><span>{period === '7d' ? 50 : 250}</span><span>0</span></div><svg className="chart" viewBox="0 0 370 102" preserveAspectRatio="none" role="img" aria-label={`${period === '7d' ? 'Weekly' : 'Monthly'} requests and alerts trending upward`}><defs><linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1638e8" stopOpacity=".35"/><stop offset="1" stopColor="#3821d6" stopOpacity=".05"/></linearGradient></defs><path d="M0 96 46 74 92 77 138 59 184 43 230 48 276 44 322 30 369 6V102H0Z" fill="url(#chart-fill)"/><path d={period === '7d' ? 'M0 96 46 74 92 77 138 59 184 43 230 48 276 44 322 30 369 6' : 'M0 94 46 83 92 68 138 72 184 49 230 33 276 39 322 18 369 4'} stroke="#34baff" strokeWidth="1.8" fill="none"/><path d="M0 99 46 84 92 88 138 76 184 72 230 80 276 65 322 62 369 34" stroke="#a436f3" strokeWidth="1.8" fill="none"/>{[0,46,92,138,184,230,276,322,369].map((x,i) => <g key={x}><circle cx={x} cy={[96,74,77,59,43,48,44,30,6][i]} r="2.3" fill="#35baff"/><circle cx={x} cy={[99,84,88,76,72,80,65,62,34][i]} r="2" fill="#a436f3"/></g>)}</svg><div className="chart-legend"><span><i/> Requests</span><span><i/> Alerts</span></div></div></div>
      </div>
    </section>

    {toast && <div className="toast" role="status"><span className="status-check"><Icon name="check" size={13}/></span>{toast}<button aria-label="Dismiss notification" onClick={() => setToast('')}><Icon name="close" size={16}/></button></div>}
    {modal && <div className="modal-backdrop" onClick={() => setModal(null)}><section className={`modal ${modal === 'sos' ? 'emergency-modal' : ''}`} role="dialog" aria-modal="true" aria-labelledby="modal-title" ref={modalRef} tabIndex={-1} onClick={event => event.stopPropagation()}><button className="modal-close" aria-label="Close dialog" onClick={() => setModal(null)}><Icon name="close" size={21}/></button><div className="modal-brand"><Logo/><span>INTERACTIVE PREVIEW</span></div>
      {modal === 'shelters' && <><h2 id="modal-title">Find a safe place.</h2><p className="modal-intro">Verified spaces. Real people ready to help.</p><div className="filters"><label><Icon name="search" size={16}/><input placeholder="Search by city..." value={city} onChange={event => setCity(event.target.value)}/></label><button className={womenOnly ? 'filter active-filter' : 'filter'} onClick={() => setWomenOnly(!womenOnly)}><Icon name="shield" size={15}/> Women-safe</button></div><div className="listing-list">{shelters.filter(s => s.city.toLowerCase().includes(city.toLowerCase()) && (!womenOnly || s.women)).map(s => <article className="listing" key={s.name}><div className="listing-top"><span className="verified-tag"><Icon name="shield" size={13}/> Verified NGO</span><span className="rating"><Icon name="star" size={12}/> {s.rating}</span></div><h3>{s.name}</h3><p><Icon name="pin" size={13}/> {s.area}, {s.city}</p><div className="listing-bottom"><span><b>{s.beds} beds available</b>{s.women && ' · Women-safe'}</span><button className="primary purple-button" disabled={requested.includes(s.name)} onClick={() => { setRequested(items => [...items, s.name]); notify('Demo request added to My Requests. No real shelter was contacted.') }}>{requested.includes(s.name) ? 'Requested' : 'Request help'}<Icon name="arrow" size={13}/></button></div><small>Exact address is shared only after acceptance. Updated 20 min ago.</small></article>)}{shelters.filter(s => s.city.toLowerCase().includes(city.toLowerCase()) && (!womenOnly || s.women)).length === 0 && <p className="empty-state">No shelters match this search. Try a nearby city.</p>}</div></>}
      {modal === 'sos' && <><div className="emergency-heading"><Icon name="alert" size={30}/><h2 id="modal-title">Emergency SOS</h2></div><p className="emergency-warning">In immediate danger? Call <a href="tel:112">112</a> now.<br/>WarBridge cannot guarantee an emergency response.</p><p className="modal-intro">This is a preview. Submitting this form does not send a real SOS or contact an NGO.</p><form className="modal-form" onSubmit={event => { event.preventDefault(); setRequests(items => [{ id: Date.now(), title: 'Guest SOS · Demo', city: 'Location provided privately', time: 'Just now', icon: 'alert', urgent: true, accepted: false }, ...items]); setModal(null); notify('Demo SOS added to the NGO panel only. For real help, call 112.') }}><label>Name <span>(optional)</span><input placeholder="How should we address you?"/></label><label>Phone <span>(optional)</span><input type="tel" placeholder="A number an NGO can reach you on"/></label><label>Your location <span>(optional)</span><textarea placeholder="City, area or nearby landmark. Do not share sensitive details."/></label><button className="accept-button" type="submit"><Icon name="alert" size={18}/> Send demo SOS</button></form></>}
      {modal === 'alerts' && <><h2 id="modal-title">Community alerts</h2><p className="modal-intro">The latest updates from verified partners. Demo content only.</p><div className="listing-list">{alerts.map((text, i) => <article className="listing alert-listing" key={`${text}-${i}`}><span className="alert-circle"><Icon name="megaphone"/></span><div><span className="verified-tag">Hope Foundation · Verified NGO</span><h3>{text}</h3><small>{i === 0 ? 'Just updated' : 'Today'} · Expires in 24 hours</small></div></article>)}</div></>}
      {modal === 'services' && <><h2 id="modal-title">Everyday essentials.</h2><p className="modal-intro">Food and healthcare from verified community partners.</p>{[{ name: 'Community Kitchen', icon: 'people' as IconName, text: 'Fresh meals · Indiranagar, Bengaluru', hours: 'Open daily · 8 AM – 8 PM' }, { name: 'Hope Medical Centre', icon: 'medical' as IconName, text: 'Primary care · Whitefield, Bengaluru', hours: 'Open daily · 9 AM – 6 PM' }].map(s => <article className="listing service-listing" key={s.name}><Icon name={s.icon} size={30}/><div><span className="verified-tag">Verified service · Demo listing</span><h3>{s.name}</h3><p>{s.text}</p><small>{s.hours} · Updated today</small></div></article>)}</>}
      {modal === 'helplines' && <><h2 id="modal-title">You don’t have to face it alone.</h2><p className="modal-intro">India emergency helplines. Tap a number to call directly.</p><Helplines full/><p className="privacy-note"><Icon name="shield" size={17}/> In an emergency, call a helpline first. WarBridge is a coordination tool, not an emergency service.</p></>}
      {modal === 'requests' && <><h2 id="modal-title">Help requests</h2><p className="modal-intro">Demo activity across the preview. In production, each role can see only its permitted requests.</p><article className="listing"><span className="verified-tag"><Icon name="check" size={13}/> Accepted</span><h3>Hope Community Shelter</h3><p>Shelter assistance · Bengaluru</p><small>Accepted 21 Nov, 12:10 PM · Awaiting host confirmation</small></article>{requested.map(name => <article className="listing" key={name}><span className="pending-tag">Pending</span><h3>{name}</h3><p>Your demo request is awaiting an NGO’s response.</p><button className="outline-button" onClick={() => setRequested(items => items.filter(item => item !== name))}>Cancel request</button></article>)}{requests.map(r => <article className="listing request-modal-row" key={r.id}><div><span className={r.accepted ? 'verified-tag' : 'pending-tag'}>{r.accepted ? 'Accepted' : 'Pending'}</span><h3>{r.title}</h3><p>{r.city} · {r.time}</p></div><button className="outline-button" onClick={() => { setSelectedRequest(r); open('request-detail') }}>View details</button></article>)}</>}
      {modal === 'request-detail' && selectedRequest && <><h2 id="modal-title">{selectedRequest.title}</h2><p className="modal-intro">{selectedRequest.city} · {selectedRequest.time}</p><article className="listing"><span className="pending-tag">Demo request</span><h3>A person is looking for support</h3><p>Review the request and confirm capacity before accepting. Personal contact details are not included in this public prototype.</p><small>All access decisions must be made by a verified human.</small></article><button className="primary" onClick={() => { accept(selectedRequest.id); setModal(null) }}>Accept demo request <Icon name="check" size={16}/></button></>}
      {modal === 'verification' && <><h2 id="modal-title">Partner verification</h2><p className="modal-intro">Review a partner before granting access to sensitive actions.</p><article className="listing"><span className="pending-tag">Awaiting review</span><h3>{selectedOrg}</h3><p>Review identity documents, organisation registration, references, and contact details before approving.</p><p className="privacy-note">No documents are stored in this prototype. Approval only updates the demo panel.</p></article><div className="button-row"><button className="approve-button" onClick={() => { const org = verifications.find(v => v.name === selectedOrg); if (org) decide(org.id, true); setModal(null) }}>Approve demo partner</button><button className="reject-button" onClick={() => { const org = verifications.find(v => v.name === selectedOrg); if (org) decide(org.id, false); setModal(null) }}>Reject</button></div></>}
      {modal === 'signin' && <><h2 id="modal-title">A place for everyone.</h2><p className="modal-intro">Explore the role-based dashboards in this interactive preview. These are demo views, not authenticated accounts.</p><div className="role-options">{[{ role: 'Displaced person', text: 'Find support and track your requests', theme: 'green', target: 'displaced' as const }, { role: 'NGO partner', text: 'Coordinate help for your community', theme: 'red', target: 'ngo' as const }, { role: 'Administrator', text: 'Review partners and keep people safe', theme: 'blue', target: 'admin' as const }].map(item => <button key={item.role} className={`role-option ${item.theme}`} onClick={() => { setModal(null); setView(item.target); notify(`Exploring the ${item.role.toLowerCase()} demo panel.`) }}><span className="stat-icon"><Icon name={item.theme === 'blue' ? 'shield' : item.theme === 'red' ? 'people' : 'user'} size={24}/></span><span><strong>{item.role}</strong><small>{item.text}</small></span><Icon name="arrow"/></button>)}</div></>}
      {modal === 'ratings' && <><h2 id="modal-title">Share your experience.</h2><p className="modal-intro">Ratings are available after a completed request. Try this demo review for a previous completed stay.</p><article className="listing"><span className="verified-tag">Completed stay · Demo</span><h3>New Beginnings Shelter</h3><div className="star-picker">{[1,2,3,4,5].map(value => <button key={value} aria-label={`Rate ${value} stars`} className={rating >= value ? 'filled' : ''} onClick={() => setRating(value)}><Icon name="star" size={30}/></button>)}</div><button className="primary" disabled={!rating} onClick={() => { notify(`Your ${rating}-star demo review has been saved for this session.`); setModal(null) }}>Save demo rating</button></article></>}
      {modal === 'reports' && <><h2 id="modal-title">Help keep the community safe.</h2><p className="modal-intro">Report a suspicious or unsafe listing. This demo does not submit real reports.</p><form className="modal-form" onSubmit={event => { event.preventDefault(); notify('Demo report recorded. No real report was sent.'); setModal(null) }}><label>Listing name<input required placeholder="Name of shelter, room or service"/></label><label>What happened?<textarea required minLength={5} placeholder="Describe your concern (at least 5 characters)"/></label><button className="primary" type="submit">Submit demo report <Icon name="arrow" size={16}/></button></form></>}
      {modal === 'audit' && <><h2 id="modal-title">Trust & safety activity</h2><p className="modal-intro">Illustrative audit log. Production audit history requires a connected, protected backend.</p>{['Admin verified Helping Hands NGO · Today, 10:42 AM', 'Report opened for Fake Shelter Listing · Today, 10:36 AM', 'Hope Foundation published a shelter alert · Today, 10:32 AM'].map(item => <div className="audit-item" key={item}><Icon name="shield" size={18}/>{item}</div>)}</>}
      {modal === 'settings' && <><h2 id="modal-title">Preview settings</h2><p className="modal-intro">WarBridge brings communities together through verified human support.</p><article className="listing"><h3>Region</h3><p>India · Emergency numbers 112, 181 and 1098</p><h3>Language</h3><p>English · Arabic and Hindi require native review before release.</p><h3>Privacy</h3><p>No personal information is sent or permanently stored by this interactive preview.</p></article><button className="outline-button" onClick={() => { setModal(null); notify('You are viewing the public WarBridge demo.') }}><Icon name="logout" size={15}/> Return to preview</button></>}
      {(modal === 'about' || modal === 'donate') && <><h2 id="modal-title">{modal === 'donate' ? 'Together, we can rebuild.' : 'A bridge. Never a gatekeeper.'}</h2><p className="modal-intro">WarBridge connects people in need with shelters, food, healthcare and verified humans who can help.</p><div className="about-values"><div><Icon name="shield" size={26}/><h3>Safety comes first</h3><p>Exact addresses stay private until a request is accepted by a verified partner.</p></div><div><Icon name="people" size={26}/><h3>People make decisions</h3><p>NGOs, hosts and shelters make every access decision. The app helps coordinate.</p></div><div><Icon name="heart" size={26}/><h3>Help without barriers</h3><p>Emergency helplines and verified public resources are available without an account.</p></div></div><div className="privacy-note">Visual, session-only prototype. No live SOS, authentication, donations, or permanent records. For immediate help in India, call 112.</div></>}
    </section></div>}
  </main></div>
}
