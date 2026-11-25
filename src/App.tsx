import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { api } from './api'

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
type AuthUser = { id: number; name: string; email: string; role: 'DISPLACED' | 'HOST' | 'NGO' | 'ADMIN'; verified: boolean }
type VerificationItem = { id: number; name: string; role: string; time: string; created_at?: string }
type AuditEntry = { action: string; target_type: string | null; target_id: number | null; created_at: string }
type ApiShelter = {
  id: number
  name: string
  city: string
  area: string
  beds_available: number
  women_safe: number
  rating: number
  rating_count: number
  updated_at: string
}
type ApiService = {
  id: number
  name: string
  category: string
  city: string
  opening_hours: string | null
  contact: string | null
  updated_at: string
}

export default function App() {
  const [view, setView] = useState<View>('home')
  const [modal, setModal] = useState<Modal>(null)
  const [toast, setToast] = useState('')
  const [requests, setRequests] = useState<RequestItem[]>([])
  const [verifications, setVerifications] = useState<VerificationItem[]>([])
  const [adminTab, setAdminTab] = useState('Pending Verifications')
  const [alertText, setAlertText] = useState('')
  const [alerts, setAlerts] = useState<string[]>([])
  const [apiShelters, setApiShelters] = useState<ApiShelter[]>([])
  const [apiServices, setApiServices] = useState<ApiService[]>([])
  const [city, setCity] = useState('')
  const [womenOnly, setWomenOnly] = useState(false)
  const [requested, setRequested] = useState<string[]>([])
  const [selectedRequest, setSelectedRequest] = useState<RequestItem | null>(null)
  const [selectedOrg, setSelectedOrg] = useState('')
  const [authUser, setAuthUser] = useState<AuthUser | null>(null)
  const [authRole, setAuthRole] = useState<'NGO' | 'ADMIN'>('NGO')
  const [authMode, setAuthMode] = useState<'signin' | 'register'>('signin')
  const [authIdentity, setAuthIdentity] = useState('')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authError, setAuthError] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([])
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
  const loadRoleData = (user: AuthUser) => {
    if (user.role === 'ADMIN') {
      void Promise.all([
        api.get<{ users: VerificationItem[] }>('/api/admin/verifications'),
        api.get<{ audit: AuditEntry[] }>('/api/admin/audit'),
      ]).then(([verificationResult, auditResult]) => {
        setVerifications(verificationResult.users.map(partner => ({
          ...partner,
          time: partner.created_at ? new Date(partner.created_at).toLocaleDateString() : '',
        })))
        setAuditEntries(auditResult.audit)
      }).catch(error => notify(error instanceof Error ? error.message : 'Could not load administrator records.'))
    } else if (user.role === 'NGO') {
      void api.get<{ requests: { id: number; type: string; location_text: string | null; created_at: string; is_sos: number; status: string }[] }>('/api/requests/incoming')
        .then(result => setRequests(result.requests.map(item => ({
          id: item.id,
          title: item.is_sos ? 'Emergency request' : `${item.type} request`,
          city: item.location_text || 'Location shared privately',
          time: new Date(item.created_at).toLocaleString(),
          icon: item.is_sos ? 'alert' : 'bed',
          urgent: Boolean(item.is_sos),
          accepted: item.status === 'Accepted',
        }))))
        .catch(error => notify(error instanceof Error ? error.message : 'Could not load incoming requests.'))
    }
  }
  useEffect(() => {
    void api.get<{ user: AuthUser | null }>('/api/auth/me')
      .then(({ user }) => {
        if (!user) return
        setAuthUser(user)
        if (user.role === 'NGO' || user.role === 'ADMIN') setView(user.role === 'NGO' ? 'ngo' : 'admin')
        loadRoleData(user)
      })
      .catch(error => setAuthError(error instanceof Error ? error.message : 'Unable to restore your sign-in session.'))
  }, [])
  useEffect(() => {
    void Promise.all([
      api.get<{ shelters: ApiShelter[] }>('/api/public/shelters'),
      api.get<{ alerts: { id: number; title: string; message: string; partner_name: string }[] }>('/api/public/alerts'),
      api.get<{ services: ApiService[] }>('/api/public/services'),
    ]).then(([shelterResponse, alertResponse, serviceResponse]) => {
      setApiShelters(shelterResponse.shelters)
      setAlerts(alertResponse.alerts.map(alert => alert.message))
      setApiServices(serviceResponse.services)
    }).catch(() => {
      notify('Could not load public listings. Check that the backend is running.')
    })
  }, [])
  const open = (value: Modal) => setModal(value)
  const navigateView = (target: View) => {
    if (target === 'ngo' || target === 'admin') {
      if (authUser?.role !== target.toUpperCase()) {
        setAuthRole(target === 'ngo' ? 'NGO' : 'ADMIN')
        setAuthMode('signin')
        setAuthError('')
        setModal('signin')
        return
      }
    }
    setView(target)
  }
  const accept = (id: number) => {
    void api.post(`/api/requests/${id}/accept`).then(() => {
      setRequests(items => items.map(r => r.id === id ? { ...r, accepted: true } : r))
      notify('Request accepted.')
    }).catch(error => notify(error instanceof Error ? error.message : 'Could not accept request.'))
  }
  const decide = (id: number, approved: boolean) => {
    const org = verifications.find(v => v.id === id)
    void api.post(`/api/admin/users/${id}/${approved ? 'verify' : 'reject'}`).then(() => {
      setVerifications(items => items.filter(v => v.id !== id))
      notify(`${org?.name ?? 'Partner'} ${approved ? 'approved' : 'rejected'}.`)
    }).catch(error => notify(error instanceof Error ? error.message : 'Could not update partner.'))
  }
  const signIn = (event: FormEvent) => {
    event.preventDefault()
    setAuthError('')
    setAuthBusy(true)
    void api.post<{ user: AuthUser; csrfToken: string }>('/api/auth/login', {
      identity: authIdentity,
      password: authPassword,
      role: authRole,
    }).then(({ user, csrfToken }) => {
      api.setCsrfToken(csrfToken)
      setAuthUser(user)
      setAuthPassword('')
      setModal(null)
      setView(user.role === 'ADMIN' ? 'admin' : 'ngo')
      loadRoleData(user)
      if (user.role === 'NGO' && !user.verified) {
        notify('Your account is awaiting administrator verification. Access is read-only.')
      } else {
        notify(`Signed in as ${user.name}.`)
      }
    }).catch(error => setAuthError(error instanceof Error ? error.message : 'Sign-in failed.'))
      .finally(() => setAuthBusy(false))
  }
  const registerNgo = (event: FormEvent) => {
    event.preventDefault()
    setAuthError('')
    setAuthBusy(true)
    void api.post<{ user: AuthUser; csrfToken: string }>('/api/auth/register', {
      name: authIdentity,
      email: authEmail,
      password: authPassword,
      role: 'NGO',
    }).then(({ user, csrfToken }) => {
      api.setCsrfToken(csrfToken)
      setAuthUser(user)
      setAuthPassword('')
      setModal(null)
      setView('ngo')
      loadRoleData(user)
      notify('NGO account created. Administrator verification is required before publishing listings.')
    }).catch(error => setAuthError(error instanceof Error ? error.message : 'NGO account could not be created.'))
      .finally(() => setAuthBusy(false))
  }
  const postAlert = (event: FormEvent) => {
    event.preventDefault()
    if (!alertText.trim()) return
    void api.post('/api/alerts', { title: alertText.trim().slice(0, 200), message: alertText.trim(), type: 'Warning' })
      .then(() => {
        setAlerts(items => [alertText.trim(), ...items])
        setAlertText('')
        notify('Community alert published.')
      })
      .catch(error => notify(error instanceof Error ? error.message : 'Sign in as a verified NGO to publish alerts.'))
  }
  const navAction = (label: string) => {
    const map: Record<string, Modal> = { 'My Requests': 'requests', 'Help Requests': 'requests', 'Safety Helplines': 'helplines', Ratings: 'ratings', Reports: 'reports', Settings: 'settings', Shelters: 'shelters', Services: 'services', Alerts: 'alerts', Verification: 'verification', 'Audit Log': 'audit' }
    if (label !== 'Dashboard') open(map[label] || 'about')
  }
  function Sidebar({ role, items, active = 'Dashboard' }: { role: 'user' | 'ngo' | 'admin'; items: [IconName, string][]; active?: string }) {
    return <aside className="sidebar"><Logo /><nav aria-label={`${role} navigation`}>{items.map(([icon, label]) => <button key={label} className={`side-link ${label === active ? 'active' : ''}`} onClick={() => navAction(label)}><Icon name={icon} /><span>{label}</span></button>)}</nav><div className="sidebar-status"><span className="status-check"><Icon name="check" size={13}/></span><div><strong>{role === 'ngo' ? (authUser?.verified ? 'NGO Verified' : 'Verification Pending') : role === 'admin' ? 'System Status' : 'Verified User'}</strong><small>{role === 'ngo' ? (authUser?.verified ? 'Trusted Partner' : 'Read-only access') : role === 'admin' ? 'All systems operational' : 'Stay Safe Together'}</small></div></div></aside>
  }
  function Profile({ name, initial }: { name: string; initial: string }) {
    return <button className="profile" onClick={() => open('settings')}><span className="avatar">{initial}</span><span>{name}</span><Icon name="chevron" size={12}/></button>
  }
  function Helplines({ full = false }: { full?: boolean }) {
    return <div className={`helpline-list ${full ? 'full' : ''}`}>{([{ name: 'Women Helpline', number: '181', icon: 'phone' }, { name: 'Emergency Response', number: '112', icon: 'phone' }, { name: 'Child Helpline', number: '1098', icon: 'shield' }] as { name: string; number: string; icon: IconName }[]).map(item => <a key={item.number} href={`tel:${item.number}`}><span className="helpline-icon"><Icon name={item.icon} size={22}/></span><span>{item.name}<strong>{item.number}</strong></span></a>)}</div>
  }

  return <div className="app-shell">
    <header className="view-header"><nav className="view-navigation" aria-label="WarBridge pages">{views.map(item => <button key={item.id} aria-pressed={view === item.id} className={view === item.id ? 'current-view' : ''} onClick={() => navigateView(item.id)}>{item.label}</button>)}</nav><span className="preview-label"><span className="live-dot"/> WarBridge</span></header>
    <main className="showcase page-layout">
    <section className="panel landing purple" hidden={view !== 'home'} aria-label="WarBridge public home">
      <div className="landing-image" /><div className="orbital orbital-one"/><div className="orbital orbital-two"/>
      <header className="landing-nav"><Logo/><nav aria-label="Public navigation"><button onClick={() => open('shelters')}>Shelters</button><button onClick={() => open('services')}>Services</button><button onClick={() => open('alerts')}>Alerts</button><button onClick={() => open('about')}>About</button></nav><button className="sign-in" onClick={() => { setAuthRole('NGO'); setAuthMode('signin'); setAuthError(''); open('signin') }}>Sign In</button></header>
      <div className="hero-copy"><div className="eyebrow"><span/> A bridge to a safer tomorrow</div><h1>War<span>Bridge</span></h1><h2>Find help. <span>Stay safe.</span></h2><p>Verified shelters, food, healthcare and more —<br className="desktop-break"/> for people in need.</p><div className="hero-actions"><button className="primary purple-button" onClick={() => open('shelters')}>Find Shelters <Icon name="arrow" size={17}/></button><button className="sos-button" onClick={() => open('sos')}><Icon name="alert" size={22}/> Emergency SOS</button></div><div className="trust-row"><div><span className="trust-icon"><Icon name="shield" size={24}/></span><span>Verified<br/>Shelters</span></div><div><span className="trust-icon"><Icon name="people" size={24}/></span><span>Trusted<br/>NGOs & Hosts</span></div><div><span className="trust-icon"><Icon name="bolt" size={24}/></span><span>Real-Time<br/>Alerts</span></div></div></div>
      <span className="landing-footnote"><span className="live-dot"/> Human connection. Real hope.</span>
    </section>

    <section className="panel dashboard green" hidden={view !== 'displaced'} aria-label="Displaced user dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="user" items={[['home', 'Dashboard'], ['requests', 'My Requests'], ['phone', 'Safety Helplines'], ['star', 'Ratings'], ['report', 'Reports'], ['settings', 'Settings']]}/>
      <div className="dashboard-main user-main">
        <div className="topbar"><span className="workspace-label">YOUR SAFE SPACE</span><div className="topbar-right"><button className="notification" aria-label="View notifications" onClick={() => open('alerts')}><Icon name="bell"/><span>{alerts.length}</span></button><Profile name="User" initial="U"/></div></div>
        <div className="welcome"><div><h2>Welcome back!</h2><p>You’re not alone. Help is here.</p></div><span className="verified-badge"><Icon name="shield" size={16}/> Verified User</span></div>
        <div className="stats-grid"><div className="stat"><span className="stat-icon"><Icon name="home" size={31}/></span><div><strong>0</strong><small>Active Requests</small></div></div><div className="stat"><span className="stat-icon gold"><Icon name="star" size={30}/></span><div><strong>0.0</strong><small>Your Rating</small></div></div><div className="stat"><span className="stat-icon"><Icon name="people" size={31}/></span><div><strong>0</strong><small>Reports Filed</small></div></div></div>
        <div className="user-middle"><div className="surface help-progress"><div className="section-heading"><h3>Your Help Requests</h3><button className="text-link" onClick={() => open('requests')}>View all <Icon name="arrow" size={13}/></button></div><div className="empty-state"><p>Your request activity will appear here.</p></div></div><div className="surface helplines-card"><h3>Safety Helplines</h3><Helplines/><button className="text-link helplines-more" onClick={() => open('helplines')}>View More <Icon name="arrow" size={11}/></button></div></div>
        <div className="impact-banner"><div className="banner-art"><Icon name="heart" size={64}/></div><div><h3>Together, we can rebuild.</h3><p>Support. Shelter. Hope.</p></div><button className="primary" onClick={() => open('donate')}>Get involved <Icon name="arrow" size={13}/></button></div>
      </div>
    </section>

    <section className="panel dashboard red" hidden={view !== 'ngo'} aria-label="NGO dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="ngo" items={[['home', 'Dashboard'], ['home', 'Help Requests'], ['bed', 'Shelters'], ['medical', 'Services'], ['megaphone', 'Alerts'], ['report', 'Reports'], ['settings', 'Settings']]}/>
      <div className="dashboard-main ngo-main"><div className="topbar"><span className="workspace-label">PARTNER WORKSPACE</span><Profile name={authUser?.name || 'Partner'} initial={(authUser?.name || 'P').slice(0, 1).toUpperCase()}/></div><div className="welcome"><div><h2>NGO Dashboard</h2><p>Provide help. Make a difference.</p></div></div>
        <div className="stats-grid ngo-stats"><div className="stat"><span className="stat-icon violet"><Icon name="home" size={31}/></span><div><strong>0</strong><small>Shelters Listed</small></div></div><div className="stat"><span className="stat-icon lime"><Icon name="people" size={31}/></span><div><strong>0</strong><small>People Assisted</small></div></div><div className="stat"><span className="stat-icon danger"><Icon name="alert" size={31}/></span><div><strong>{requests.filter(r => !r.accepted).length}</strong><small>Emergency Requests</small></div></div></div>
        <div className="ngo-middle"><div className="surface incoming"><div className="section-heading"><h3>Incoming Help Requests</h3><button className="text-link" onClick={() => open('requests')}>View all <Icon name="arrow" size={12}/></button></div><div className="request-list">{requests.length ? requests.map(request => <div className="request-row" key={request.id}><span className={`request-icon ${request.urgent ? 'urgent' : ''}`}>{request.urgent ? 'SOS' : <Icon name={request.icon} size={28}/>}</span><div className="request-info"><strong>{request.title}{request.urgent && <i/>}</strong><small>{request.city} · {request.time}</small></div><button className="outline-button" onClick={() => { setSelectedRequest(request); open('request-detail') }}>View</button><button className={`accept-button ${request.accepted ? 'accepted' : ''}`} disabled={request.accepted} onClick={() => accept(request.id)}>{request.accepted ? 'Accepted' : 'Accept'}</button></div>) : <p className="empty-state">No incoming requests.</p>}</div></div><form className="surface post-alert" onSubmit={postAlert}><h3>Post an Alert</h3><div className="alert-hint"><Icon name="megaphone" size={23}/><p>Share important updates<br/>with the community.</p></div><label className="sr-only" htmlFor="alert-message">Alert message</label><textarea id="alert-message" required maxLength={300} value={alertText} onChange={event => setAlertText(event.target.value)} placeholder="Type your message..."/><button className="accept-button" type="submit" disabled={!authUser?.verified}>Post Alert</button>{authUser && !authUser.verified && <small>Administrator verification is required to post alerts.</small>}</form></div>
        <div className="impact-banner ngo-banner"><div className="banner-art"><Icon name="people" size={64}/></div><div><h3>Be the bridge in someone’s journey.</h3><p>Your support makes a difference.</p></div><button className="outline-button" onClick={() => open('about')}>Learn More <Icon name="arrow" size={12}/></button></div>
      </div>
    </section>

    <section className="panel dashboard blue" hidden={view !== 'admin'} aria-label="Admin dashboard">
      <div className="dashboard-landscape"/><div className="orbital orbital-one"/>
      <Sidebar role="admin" active="Verification" items={[['home', 'Dashboard'], ['shield', 'Verification'], ['report', 'Reports'], ['requests', 'Audit Log'], ['settings', 'Settings']]}/>
      <div className="dashboard-main admin-main"><div className="topbar"><span className="workspace-label">TRUST & SAFETY</span><Profile name={authUser?.name || 'Administrator'} initial={(authUser?.name || 'A').slice(0, 1).toUpperCase()}/></div><div className="welcome"><div><h2>Admin Panel</h2><p>Verify. Monitor. Ensure Safety.</p></div><Icon name="shield" size={85} className="admin-shield"/></div>
        <div className="admin-middle"><div className="verification-section"><div className="tabs" role="tablist" aria-label="Admin lists">{['Pending Verifications', 'Reports', 'Blocked Listings'].map((tab, i) => <button key={tab} role="tab" aria-selected={adminTab === tab} onClick={() => setAdminTab(tab)} className={adminTab === tab ? 'selected' : ''}>{tab} ({i === 0 ? verifications.length : 0})</button>)}</div><div className="surface verification-list">{adminTab === 'Pending Verifications' ? verifications.length ? verifications.map(org => <div className="verification-row" key={org.id}><span className="org-icon"><Icon name="user" size={27}/></span><div className="org-info"><strong>{org.name}</strong><small>{org.role} · Registered {org.time}</small></div><button className="outline-button" onClick={() => { setSelectedOrg(org.name); open('verification') }}>View</button><button className="approve-button" onClick={() => decide(org.id, true)}>Approve</button><button className="reject-button" onClick={() => decide(org.id, false)}>Reject</button></div>) : <div className="empty-state"><Icon name="check" size={30}/><p>No pending partner verifications.</p></div> : <div className="empty-state"><p>No {adminTab.toLowerCase()} to show.</p></div>}</div></div><div className="surface activity"><div className="section-heading"><h3>Recent Activity</h3><button className="text-link" onClick={() => open('audit')}>View all <Icon name="arrow" size={11}/></button></div><p className="empty-state">Activity will appear here as records are added.</p></div></div>
        <div className="surface chart-card"><div className="section-heading"><h3>Platform Overview</h3></div><p className="empty-state">Analytics will appear after platform activity is recorded.</p></div>
      </div>
    </section>

    {toast && <div className="toast" role="status"><span className="status-check"><Icon name="check" size={13}/></span>{toast}<button aria-label="Dismiss notification" onClick={() => setToast('')}><Icon name="close" size={16}/></button></div>}
    {modal && <div className="modal-backdrop" onClick={() => setModal(null)}><section className={`modal ${modal === 'sos' ? 'emergency-modal' : ''}`} role="dialog" aria-modal="true" aria-labelledby="modal-title" ref={modalRef} tabIndex={-1} onClick={event => event.stopPropagation()}><button className="modal-close" aria-label="Close dialog" onClick={() => setModal(null)}><Icon name="close" size={21}/></button><div className="modal-brand"><Logo/><span>WARBRIDGE</span></div>
      {modal === 'shelters' && <><h2 id="modal-title">Find a safe place.</h2><p className="modal-intro">Verified spaces. Real people ready to help.</p><div className="filters"><label><Icon name="search" size={16}/><input placeholder="Search by city..." value={city} onChange={event => setCity(event.target.value)}/></label><button className={womenOnly ? 'filter active-filter' : 'filter'} onClick={() => setWomenOnly(!womenOnly)}><Icon name="shield" size={15}/> Women-safe</button></div><div className="listing-list">{apiShelters.filter(s => s.city.toLowerCase().includes(city.toLowerCase()) && (!womenOnly || s.women_safe)).map(s => <article className="listing" key={s.id}><div className="listing-top"><span className="verified-tag"><Icon name="shield" size={13}/> Verified NGO</span><span className="rating"><Icon name="star" size={12}/> {Number(s.rating).toFixed(1)} ({s.rating_count})</span></div><h3>{s.name}</h3><p><Icon name="pin" size={13}/> {s.area}, {s.city}</p><div className="listing-bottom"><span><b>{s.beds_available} beds available</b>{Boolean(s.women_safe) && ' · Women-safe'}</span><button className="primary purple-button" disabled={requested.includes(s.name)} onClick={() => {
        void api.post('/api/requests', { shelter_id: s.id })
          .then(() => { setRequested(items => [...items, s.name]); notify('Help request submitted for review.') })
          .catch(error => notify(error instanceof Error ? error.message : 'Sign in as a Displaced user before requesting help.'))
      }}>{requested.includes(s.name) ? 'Requested' : 'Request help'}<Icon name="arrow" size={13}/></button></div><small>Exact address is shared only after acceptance. Listing updated {new Date(s.updated_at).toLocaleString()}.</small></article>)}{apiShelters.filter(s => s.city.toLowerCase().includes(city.toLowerCase()) && (!womenOnly || s.women_safe)).length === 0 && <p className="empty-state">No verified shelters are currently listed.</p>}</div></>}
      {modal === 'sos' && <><div className="emergency-heading"><Icon name="alert" size={30}/><h2 id="modal-title">Emergency SOS</h2></div><p className="emergency-warning">In immediate danger? Call <a href="tel:112">112</a> now.<br/>WarBridge cannot guarantee an emergency response.</p><p className="modal-intro">Submitting SOS creates a rate-limited request for a verified NGO. It does not replace emergency services.</p><form className="modal-form" onSubmit={event => {
        event.preventDefault()
        const form = new FormData(event.currentTarget)
        void api.post('/api/sos', { name: form.get('name'), phone: form.get('phone'), location: form.get('location'), website: form.get('website') })
          .then(() => { setModal(null); notify('SOS submitted to the NGO queue.') })
          .catch(error => notify(error instanceof Error ? error.message : 'SOS could not be submitted.'))
      }}><label>Name <span>(optional)</span><input name="name" placeholder="How should we address you?"/></label><label>Phone <span>(optional)</span><input name="phone" type="tel" placeholder="A number an NGO can reach you on"/></label><label>Your location <span>(optional)</span><textarea name="location" placeholder="City, area or nearby landmark. Do not share sensitive details."/></label><input className="sr-only" name="website" tabIndex={-1} autoComplete="off" aria-hidden="true"/><button className="accept-button" type="submit"><Icon name="alert" size={18}/> Send SOS</button></form></>}
      {modal === 'alerts' && <><h2 id="modal-title">Community alerts</h2><p className="modal-intro">Current updates published by verified partners.</p><div className="listing-list">{alerts.length ? alerts.map((text, i) => <article className="listing alert-listing" key={`${text}-${i}`}><span className="alert-circle"><Icon name="megaphone"/></span><div><span className="verified-tag">Verified community update</span><h3>{text}</h3></div></article>) : <p className="empty-state">There are no current community alerts.</p>}</div></>}
      {modal === 'services' && <><h2 id="modal-title">Everyday essentials.</h2><p className="modal-intro">Services listed by verified community partners.</p>{apiServices.length ? apiServices.map(service => <article className="listing service-listing" key={service.id}><Icon name="people" size={30}/><div><span className="verified-tag">{service.category} · Verified service</span><h3>{service.name}</h3><p>{service.city}</p><small>{service.opening_hours || 'Hours not provided'}</small></div></article>) : <p className="empty-state">No verified services are currently listed.</p>}</>}
      {modal === 'helplines' && <><h2 id="modal-title">You don’t have to face it alone.</h2><p className="modal-intro">India emergency helplines. Tap a number to call directly.</p><Helplines full/><p className="privacy-note"><Icon name="shield" size={17}/> In an emergency, call a helpline first. WarBridge is a coordination tool, not an emergency service.</p></>}
      {modal === 'requests' && <><h2 id="modal-title">Help requests</h2><p className="modal-intro">Requests are shown only to the account that owns them or is authorized to handle them.</p>{requests.length ? requests.map(r => <article className="listing request-modal-row" key={r.id}><div><span className={r.accepted ? 'verified-tag' : 'pending-tag'}>{r.accepted ? 'Accepted' : 'Pending'}</span><h3>{r.title}</h3><p>{r.city} · {r.time}</p></div><button className="outline-button" onClick={() => { setSelectedRequest(r); open('request-detail') }}>View details</button></article>) : <p className="empty-state">No help requests are available for this account.</p>}</>}
      {modal === 'request-detail' && selectedRequest && <><h2 id="modal-title">{selectedRequest.title}</h2><p className="modal-intro">{selectedRequest.city} · {selectedRequest.time}</p><article className="listing"><span className="pending-tag">Help request</span><h3>A person is looking for support</h3><p>Review the request and confirm capacity before accepting. Contact details remain private until permitted.</p><small>All access decisions must be made by a verified human.</small></article><button className="primary" onClick={() => { accept(selectedRequest.id); setModal(null) }}>Accept request <Icon name="check" size={16}/></button></>}
      {modal === 'verification' && <><h2 id="modal-title">Partner verification</h2><p className="modal-intro">Review a partner before granting access to sensitive actions.</p><article className="listing"><span className="pending-tag">Awaiting review</span><h3>{selectedOrg}</h3><p>Review identity documents, organisation registration, references, and contact details before approving.</p><p className="privacy-note">Verification decisions are recorded in the audit history.</p></article><div className="button-row"><button className="approve-button" onClick={() => { const org = verifications.find(v => v.name === selectedOrg); if (org) decide(org.id, true); setModal(null) }}>Approve partner</button><button className="reject-button" onClick={() => { const org = verifications.find(v => v.name === selectedOrg); if (org) decide(org.id, false); setModal(null) }}>Reject</button></div></>}
      {modal === 'signin' && <><h2 id="modal-title">{authMode === 'signin' ? 'Partner sign in' : 'Register your NGO'}</h2><p className="modal-intro">{authMode === 'signin' ? 'Enter the name registered with WarBridge and its password. The account must match the selected role.' : 'Create an NGO account. An administrator must verify it before it can publish listings or alerts.'}</p>{authMode === 'signin' ? <div className="tabs auth-tabs" role="tablist" aria-label="Account type"><button type="button" role="tab" aria-selected={authRole === 'NGO'} className={authRole === 'NGO' ? 'selected' : ''} onClick={() => { setAuthRole('NGO'); setAuthError('') }}>NGO</button><button type="button" role="tab" aria-selected={authRole === 'ADMIN'} className={authRole === 'ADMIN' ? 'selected' : ''} onClick={() => { setAuthRole('ADMIN'); setAuthError('') }}>Administrator</button></div> : <div className="tabs auth-tabs"><button type="button" className="selected" disabled>NGO registration</button></div>}<form className="modal-form" onSubmit={authMode === 'signin' ? signIn : registerNgo}><label>{authMode === 'register' ? 'NGO name' : authRole === 'NGO' ? 'NGO name or registered email' : 'Administrator username or email'}<input required autoComplete="username" value={authIdentity} onChange={event => setAuthIdentity(event.target.value)} placeholder={authMode === 'register' || authRole === 'NGO' ? 'Enter your NGO name' : 'Enter your admin username'}/></label>{authMode === 'register' && <label>Contact email<input required type="email" autoComplete="email" value={authEmail} onChange={event => setAuthEmail(event.target.value)} placeholder="name@organization.org"/></label>}<label>Password<input required minLength={authMode === 'register' ? 8 : undefined} type="password" autoComplete={authMode === 'register' ? 'new-password' : 'current-password'} value={authPassword} onChange={event => setAuthPassword(event.target.value)} placeholder={authMode === 'register' ? 'At least 8 characters' : 'Enter your password'}/></label>{authError && <p className="form-error" role="alert">{authError}</p>}<button className="primary purple-button" type="submit" disabled={authBusy}>{authBusy ? 'Please wait…' : authMode === 'signin' ? 'Sign in' : 'Create NGO account'} <Icon name="arrow" size={16}/></button></form>{authRole === 'NGO' && <button className="text-link" onClick={() => { setAuthMode(authMode === 'signin' ? 'register' : 'signin'); setAuthError('') }}>{authMode === 'signin' ? 'Register an NGO' : 'Already registered? Sign in'}</button>}{authMode === 'signin' && <button className="text-link" onClick={() => { setModal(null); setView('displaced') }}>Continue as a displaced person</button>}</>}
      {modal === 'ratings' && <><h2 id="modal-title">Share your experience.</h2><p className="modal-intro">You can rate a shelter after your help request is marked complete.</p><p className="empty-state">There are no completed stays available to rate.</p></>}
      {modal === 'reports' && <><h2 id="modal-title">Help keep the community safe.</h2><p className="modal-intro">Report a suspicious or unsafe listing for administrator review.</p><form className="modal-form" onSubmit={event => {
        event.preventDefault()
        const form = new FormData(event.currentTarget)
        const listingId = Number(form.get('listing_id'))
        void api.post('/api/reports', {
          listing_type: form.get('listing_type'),
          listing_id: listingId,
          reason: form.get('reason'),
        }).then(() => { notify('Your report was submitted.'); setModal(null) })
          .catch(error => notify(error instanceof Error ? error.message : 'Sign in before submitting a report.'))
      }}><label>Listing type<select name="listing_type"><option value="shelter">Shelter</option><option value="accommodation">Accommodation</option><option value="service">Service</option></select></label><label>Listing ID<input required name="listing_id" type="number" min="1" step="1" placeholder="ID shown on the listing"/></label><label>What happened?<textarea required name="reason" minLength={5} placeholder="Describe your concern (at least 5 characters)"/></label><button className="primary" type="submit">Submit report <Icon name="arrow" size={16}/></button></form></>}
      {modal === 'audit' && <><h2 id="modal-title">Trust & safety activity</h2><p className="modal-intro">Administrative actions are recorded in the audit history.</p><p className="empty-state">Sign in as an administrator to view the audit log.</p></>}
      {modal === 'settings' && <><h2 id="modal-title">Account settings</h2><p className="modal-intro">WarBridge brings communities together through verified human support.</p><article className="listing"><h3>Region</h3><p>India · Emergency numbers 112, 181 and 1098</p><h3>Language</h3><p>English</p><h3>Account</h3><p>{authUser ? `${authUser.name} · ${authUser.role}` : 'Public access'}</p></article>{authUser && <button className="outline-button" onClick={() => {
        void api.post('/api/auth/logout').then(() => api.resetCsrf()).then(() => {
          setAuthUser(null)
          setView('home')
          setModal(null)
          notify('You have signed out.')
        }).catch(error => notify(error instanceof Error ? error.message : 'Could not sign out.'))
      }}><Icon name="logout" size={15}/> Sign out</button>}</>}
      {(modal === 'about' || modal === 'donate') && <><h2 id="modal-title">{modal === 'donate' ? 'Together, we can rebuild.' : 'A bridge. Never a gatekeeper.'}</h2><p className="modal-intro">WarBridge connects people in need with shelters, food, healthcare and verified humans who can help.</p><div className="about-values"><div><Icon name="shield" size={26}/><h3>Safety comes first</h3><p>Exact addresses stay private until a request is accepted by a verified partner.</p></div><div><Icon name="people" size={26}/><h3>People make decisions</h3><p>NGOs, hosts and shelters make every access decision. The app helps coordinate.</p></div><div><Icon name="heart" size={26}/><h3>Help without barriers</h3><p>Emergency helplines and verified public resources are available without an account.</p></div></div><div className="privacy-note">For immediate help in India, call 112.</div></>}
    </section></div>}
  </main></div>
}
