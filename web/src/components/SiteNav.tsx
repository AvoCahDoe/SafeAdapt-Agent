import Link from "next/link";

const links = [
  { href: "/", label: "Home" },
  { href: "/results", label: "Results" },
  { href: "/try", label: "Try it" },
  { href: "/docs", label: "Docs" },
];

export function SiteNav() {
  return (
    <header className="site-nav">
      <Link href="/" className="nav-brand">
        SafeAdapt
      </Link>
      <nav className="nav-links" aria-label="Primary">
        {links.map((l) => (
          <Link key={l.href} href={l.href}>
            {l.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
