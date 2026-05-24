import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

function linkHaystack(link) {
  return [
    link.label,
    link.aria,
    link.opsSubGroup,
    link.group,
    link.opsSearch,
    link.to,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function filterGroupedOpsLinks(groupedOpsLinks, query) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return groupedOpsLinks;
  return groupedOpsLinks
    .map((entry) => {
      const links = entry.links.filter((link) => linkHaystack(link).includes(q));
      return links.length ? { ...entry, links } : null;
    })
    .filter(Boolean);
}

/**
 * Painel OPS com busca instantânea e subgrupos (`opsSubGroup`).
 */
export default function OpsMenuPanel({
  groupedOpsLinks,
  clusterOpsLinksBySubGroup,
  onNavigate,
  className = "nav-ops-panel",
  id = "ops-menu-search",
  variant = "dropdown",
}) {
  const linkClass = variant === "mobile" ? "mobile-nav-link mobile-nav-link--dev" : "nav-ops-item";
  const groupTitleClass =
    variant === "mobile" ? "ops-group-title ops-group-title--mobile" : "ops-group-title";
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () => filterGroupedOpsLinks(groupedOpsLinks, query),
    [groupedOpsLinks, query],
  );
  const totalMatches = filtered.reduce((n, g) => n + g.links.length, 0);

  return (
    <div className={className} role="menu" aria-label="Menu OPS">
      <div className="nav-ops-search-wrap">
        <label className="sr-only" htmlFor={id}>
          Buscar ferramentas OPS
        </label>
        <input
          id={id}
          type="search"
          className="nav-ops-search"
          placeholder="Buscar OPS… (ex.: payments, fiscal, locker)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
          spellCheck={false}
          onKeyDown={(e) => e.stopPropagation()}
        />
        {query.trim() ? (
          <p className="nav-ops-search-hint" aria-live="polite">
            {totalMatches === 0 ? "Nenhum resultado" : `${totalMatches} tela(s)`}
          </p>
        ) : null}
      </div>

      {filtered.map((groupEntry) => (
        <div key={groupEntry.group} className="nav-ops-group-block">
          <div className={groupTitleClass}>{groupEntry.group}</div>
          {clusterOpsLinksBySubGroup(groupEntry.links).map((bucket, bidx) => (
            <div key={`${groupEntry.group}-sg-${bidx}`} className="nav-ops-subgroup-block">
              {bucket.subGroupLabel ? (
                <div className="ops-subgroup-title">{bucket.subGroupLabel}</div>
              ) : null}
              {bucket.links.map((link) => (
                <Link
                  key={link.to}
                  className={linkClass}
                  to={link.to}
                  title={link.aria || link.label}
                  onClick={onNavigate}
                >
                  <span>{link.label}</span>
                  {link.newTag ? <span className="nav-new-badge">{link.newTag}</span> : null}
                </Link>
              ))}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
