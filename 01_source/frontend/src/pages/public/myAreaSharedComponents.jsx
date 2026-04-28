import React from "react";
import { Link } from "react-router-dom";

export function PageHeader({
  title,
  subtitle,
  ctaTo = "/comprar",
  ctaLabel = "✨ Novo Pedido",
  headerStyle,
  titleStyle,
  subtitleStyle,
  ctaStyle,
}) {
  return (
    <header style={headerStyle}>
      <div>
        <h1 style={titleStyle}>{title}</h1>
        <p style={subtitleStyle}>{subtitle}</p>
      </div>
      <Link to={ctaTo} style={ctaStyle}>
        {ctaLabel}
      </Link>
    </header>
  );
}

export function StatusChips({
  options,
  activeKey,
  counts,
  onSelect,
  wrapStyle,
  chipStyle,
  activeChipStyle,
}) {
  return (
    <div style={wrapStyle} role="tablist" aria-label="Filtros por status">
      {options.map((option) => (
        <button
          key={option.key}
          type="button"
          onClick={() => onSelect(option.key)}
          style={{
            ...chipStyle,
            ...(activeKey === option.key ? activeChipStyle : {}),
          }}
          aria-pressed={activeKey === option.key}
        >
          {option.label} ({counts?.[option.key] ?? 0})
        </button>
      ))}
    </div>
  );
}

export function SkeletonCard({
  containerStyle,
  headerStyle,
  bodyStyle,
  lineStyle,
  headerLeftStyle,
  headerRightStyle,
  lineCount = 3,
}) {
  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <div style={headerLeftStyle || lineStyle}></div>
        <div style={headerRightStyle || lineStyle}></div>
      </div>
      <div style={bodyStyle}>
        {Array.from({ length: lineCount }).map((_, index) => (
          <div key={index} style={lineStyle}></div>
        ))}
      </div>
    </div>
  );
}

export function ErrorCard({
  title,
  message,
  icon = "⚠️",
  containerStyle,
  iconStyle,
  textStyle,
  action,
}) {
  return (
    <div style={containerStyle}>
      <div style={iconStyle}>{icon}</div>
      <div>
        <strong>{title}</strong>
        <p style={textStyle}>{message}</p>
        {action || null}
      </div>
    </div>
  );
}

export function EmptyStateBlock({
  title,
  description,
  icon = "📭",
  ctaTo,
  ctaLabel,
  containerStyle,
  iconStyle,
  titleStyle,
  descriptionStyle,
  buttonStyle,
}) {
  return (
    <div style={containerStyle}>
      <div style={iconStyle}>{icon}</div>
      <h3 style={titleStyle}>{title}</h3>
      <p style={descriptionStyle}>{description}</p>
      {ctaTo && ctaLabel ? (
        <Link to={ctaTo} style={buttonStyle}>
          {ctaLabel}
        </Link>
      ) : null}
    </div>
  );
}

export function SummaryMetrics({
  items,
  sectionStyle,
  cardStyle,
  labelStyle,
  valueStyle,
  sectionAriaLabel = "Resumo",
}) {
  return (
    <section style={sectionStyle} aria-label={sectionAriaLabel}>
      {items.map((item) => (
        <article key={item.key} style={cardStyle}>
          <span style={labelStyle}>{item.label}</span>
          <strong style={valueStyle}>{item.value}</strong>
        </article>
      ))}
    </section>
  );
}
