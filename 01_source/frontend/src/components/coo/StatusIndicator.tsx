import React from 'react'

export type CooOperationalStatus = 'operational' | 'attention' | 'critical' | 'maintenance'

export interface StatusIndicatorProps {
  status: CooOperationalStatus
  label?: string
  size?: 'small' | 'medium' | 'large'
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  label,
  size = 'medium',
}) => {
  const sizeMap = { small: 8, medium: 12, large: 16 } as const
  const diameter = sizeMap[size]

  const getStatusClass = (): string => {
    switch (status) {
      case 'operational':
        return 'status-operational'
      case 'attention':
        return 'status-attention'
      case 'critical':
        return 'status-critical'
      case 'maintenance':
        return 'status-maintenance'
      default:
        return 'status-operational'
    }
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div
        className={getStatusClass()}
        style={{ width: diameter, height: diameter, minWidth: diameter, minHeight: diameter }}
      />
      {label ? <span className="coo-status-label">{label}</span> : null}
    </div>
  )
}
