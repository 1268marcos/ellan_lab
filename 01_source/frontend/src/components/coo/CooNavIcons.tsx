import type { SVGProps } from 'react'

function common(p: SVGProps<SVGSVGElement>, viewBox: string) {
  return {
    width: p.width ?? 18,
    height: p.height ?? 18,
    viewBox,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
    ...p,
  } as SVGProps<SVGSVGElement>
}

export function IconRocket(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M4.5 16.5c1-5 4-10 11-11 1 7 6 10 11 11-5 1-10 4-11 11-1-7-6-10-11-11Z" />
      <path d="m9 15 3 3" />
    </svg>
  )
}

export function IconBox(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
      <path d="M3.27 6.96 12 12.01l8.73-5.05M12 22.08V12" />
    </svg>
  )
}

export function IconTruck(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2" />
      <path d="M15 18H9" />
      <path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14" />
      <circle cx="17" cy="18" r="2" />
      <circle cx="7" cy="18" r="2" />
    </svg>
  )
}

export function IconChart(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M3 3v18h18" />
      <path d="m18 9-5 5-4-4-3 3" />
    </svg>
  )
}

export function IconCheck(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <path d="m22 4-10 10-3-3" />
    </svg>
  )
}

export function IconBars(p: SVGProps<SVGSVGElement>) {
  return (
    <svg {...common(p, '0 0 24 24')}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  )
}
