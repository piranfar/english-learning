import { Link } from 'react-router-dom'
import { developerModeStorageKey } from '../../utils/developerMode'

export default function AdminHome() {
  return (
    <div className="page admin-home">
      <header className="page-header">
        <h2>Admin dashboard</h2>
        <p className="page-lead">Manage prompts and developer settings.</p>
      </header>

      <section className="card card-compact">
        <h3>Developer mode</h3>
        <p className="muted">
          Provider selectors on learner pages are hidden by default. To reveal them in the browser console, run:
        </p>
        <pre className="admin-dev-mode-snippet">
          {`localStorage.setItem('${developerModeStorageKey()}', 'true'); location.reload();`}
        </pre>
        <p className="muted">
          To hide them again:{' '}
          <code>{`localStorage.removeItem('${developerModeStorageKey()}'); location.reload();`}</code>
        </p>
      </section>

      <section className="card-grid">
        <Link to="/admin/prompts" className="card admin-card-link">
          <h3>Prompt management</h3>
          <p className="muted">
            Edit AI system prompts for grammar, speaking, writing, and other tracks.
          </p>
        </Link>
        <a
          href="http://127.0.0.1:8000/admin/"
          className="card admin-card-link"
          target="_blank"
          rel="noreferrer"
        >
          <h3>Django admin</h3>
          <p className="muted">
            User profiles, vocabulary seeds, lesson topics, and database records.
          </p>
        </a>
      </section>
    </div>
  )
}
