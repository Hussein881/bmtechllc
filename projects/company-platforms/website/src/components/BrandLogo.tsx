type BrandLogoProps = {
  full?: boolean
}

export function BrandLogo({ full = false }: BrandLogoProps) {
  return (
    <span className={`brand-logo${full ? ' brand-logo--full' : ''}`}>
      <svg
        className="brand-logo__mark"
        viewBox="0 0 164 116"
        aria-hidden="true"
        focusable="false"
      >
        <path
          className="brand-logo__stroke brand-logo__stroke--light"
          d="M52 10h57c25 0 41 9 41 25s-16 26-41 26H98m0 0h12c27 0 44 10 44 26s-17 19-44 19H98"
        />
        <path className="brand-logo__stroke brand-logo__stroke--middle" d="M26 61h72" />
        <path className="brand-logo__stroke brand-logo__stroke--accent" d="M2 106h96" />
      </svg>

      <span className="brand-logo__type">
        <span className="brand-logo__name"><b>BM</b><span>Tech</span></span>
        {full ? <span className="brand-logo__full-name">Benchmark Technology</span> : null}
      </span>
    </span>
  )
}
