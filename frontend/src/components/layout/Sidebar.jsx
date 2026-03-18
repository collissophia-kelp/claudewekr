import { NavLink } from 'react-router-dom';
import { Search, LayoutDashboard, Globe, Settings, Waves } from 'lucide-react';

const links = [
  { to: '/analyse', icon: Search, label: 'Analyse' },
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/directory', icon: Globe, label: 'Directory' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar() {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="flex items-center gap-2">
          <Waves size={24} style={{ color: 'var(--interactive)' }} />
          <div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>Kelp Blue</div>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Strategic Dashboard</div>
          </div>
        </div>
      </div>

      <div className="sidebar-nav">
        {links.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="flex items-center gap-2">
          <div
            style={{
              width: 8, height: 8, borderRadius: '50%',
              background: 'var(--stimblue-green)',
            }}
          />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
            STIMBLUE+
          </span>
        </div>
      </div>
    </nav>
  );
}
