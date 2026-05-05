import type { ReactNode } from 'react'
import Shortcuts from '../components/Shortcuts'
import Menu from './Menu'

export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <div className="ellan-shell">
      <div className="flex h-full">
        <Menu />
        <main className="ellan-content flex-1">{children}</main>
      </div>
      <Shortcuts />
    </div>
  )
}
