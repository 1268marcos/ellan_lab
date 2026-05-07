import React from 'react'

export interface PlaceholderProps {
  title: string
  description?: string
  /** Segmento após `/v1/coo/` para referência (ex: `health/pickups`). */
  endpointSlug?: string
}

export const Placeholder: React.FC<PlaceholderProps> = ({ title, description, endpointSlug }) => {
  const slug = endpointSlug ?? title.toLowerCase().replace(/\s+/g, '/')
  return (
    <div style={{ padding: '40px', textAlign: 'center' }}>
      <h2 className="coo-heading-section" style={{ color: '#2C5282' }}>
        {title}
      </h2>
      <p className="coo-text-muted" style={{ marginTop: '16px' }}>
        {description ?? 'Em desenvolvimento'}
      </p>
      <div
        style={{
          marginTop: '32px',
          padding: '40px',
          background: '#F7FAFC',
          borderRadius: '8px',
          fontFamily: 'ui-monospace, monospace',
          textAlign: 'left',
          maxWidth: 560,
          marginLeft: 'auto',
          marginRight: 'auto',
        }}
      >
        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{`GET /api/v1/coo/${slug}`}</pre>
        <pre style={{ margin: '8px 0 0', whiteSpace: 'pre-wrap' }}>Status: MVP — implementação em andamento</pre>
      </div>
    </div>
  )
}
