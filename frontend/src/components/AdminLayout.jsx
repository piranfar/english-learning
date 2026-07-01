import { Link, NavLink, Outlet } from 'react-router-dom'

const ADMIN_NAV = [
  { to: '/admin', label: 'Admin home', end: true },
  { to: '/admin/prompts', label: 'Prompt management' },
]

export default function AdminLayout() {
  return (
    <div className="admin-layout">
      <header className="admin-layout-header">
        <div>
          <h1 className="admin-layout-title">FluentBridge Admin</h1>
          <p className="muted">Developer and staff tools — not shown to learners.</p>
        </div>
        <div className="btn-group">
          <Link to="/dashboard" className="btn btn-secondary btn-sm">
            Back to app
          </Link>
          <a
            href="http://127.0.0.1:8000/admin/"
            className="btn btn-secondary btn-sm"
            target="_blank"
            rel="noreferrer"
          >
            Django admin
          </a>
        </div>
      </header>

      <nav className="admin-nav" aria-label="Admin navigation">
        {ADMIN_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              isActive ? 'admin-nav-link admin-nav-link-active' : 'admin-nav-link'
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="admin-layout-content">
        <Outlet />
      </div>
    </div>
  )
}
