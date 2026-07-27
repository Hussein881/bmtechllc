import { footer } from '../content/site'
import { BrandLogo } from './BrandLogo'

export function Footer() {
  return (
    <footer className="footer">
      <div className="shell">
        <div className="footer__grid">
          <div>
            <a className="wordmark" href="#top" aria-label="BMTech — Benchmark Technology, home">
              <BrandLogo full />
            </a>
            <p className="muted footer__blurb">{footer.blurb}</p>
          </div>

          {footer.columns.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h2>{column.title}</h2>
              <ul>
                {column.links.map((link) => (
                  <li key={link.href + link.label}>
                    <a href={link.href}>{link.label}</a>
                  </li>
                ))}
              </ul>
              {column.note ? <p className="muted footer__note">{column.note}</p> : null}
            </nav>
          ))}
        </div>

        <div className="footer__legal">
          <p>{footer.legal}</p>
          <p>© {new Date().getFullYear()} BMTech. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
