import React from 'react'

export interface GaugeChartProps {
  value: number
  max: number
  label: string
  color?: string
}

export const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  max,
  label,
  color = '#2C5282',
}) => {
  const safeMax = max > 0 ? max : 1
  const percentage = Math.min(100, Math.max(0, (value / safeMax) * 100))
  const degrees = (percentage / 100) * 360

  return (
    <div style={{ textAlign: 'center' }}>
      <div
        className="coo-gauge"
        style={{
          background: `conic-gradient(${color} 0deg ${degrees}deg, #E2E8F0 ${degrees}deg 360deg)`,
        }}
      >
        <div className="coo-gauge-inner">{Math.round(percentage)}%</div>
      </div>
      <div style={{ marginTop: '12px', fontSize: '13px', color: '#718096' }}>{label}</div>
    </div>
  )
}
