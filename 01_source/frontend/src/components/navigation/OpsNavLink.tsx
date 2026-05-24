import { Link, useLocation } from 'react-router-dom'
import { isOpsNavItemActive } from '../../navigation/opsNavMatch'

type Props = {
  to: string
  className: string
  children: React.ReactNode
}

/** Navegação explícita pathname + search (evita falhas de NavLink só com query). */
export default function OpsNavLink({ to, className, children }: Props) {
  const location = useLocation()
  const active = isOpsNavItemActive(to, location)
  const [pathname, searchPart] = to.split('?')
  const search = searchPart ? `?${searchPart}` : ''

  return (
    <Link to={{ pathname, search }} className={className(active)} aria-current={active ? 'page' : undefined}>
      {children}
    </Link>
  )
}
