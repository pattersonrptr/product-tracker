/**
 * Collapsible navigation sidebar.
 *
 * User section:   Dashboard, My Alerts, Products
 * Admin section:  Users, Search Configs, Source Websites
 */

import DashboardIcon from '@mui/icons-material/Dashboard'
import InventoryIcon from '@mui/icons-material/Inventory'
import ManageSearchIcon from '@mui/icons-material/ManageSearch'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import PeopleIcon from '@mui/icons-material/People'
import PublicIcon from '@mui/icons-material/Public'
import Divider from '@mui/material/Divider'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import ListSubheader from '@mui/material/ListSubheader'
import Tooltip from '@mui/material/Tooltip'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export const SIDEBAR_WIDTH_EXPANDED = 220
export const SIDEBAR_WIDTH_COLLAPSED = 60

interface SidebarProps {
  open: boolean
}

const USER_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
  { label: 'My Alerts', path: '/alerts', icon: <NotificationsActiveIcon /> },
  { label: 'Products', path: '/products', icon: <InventoryIcon /> },
] as const

const ADMIN_ITEMS = [
  { label: 'Users', path: '/admin/users', icon: <PeopleIcon /> },
  { label: 'Search Configs', path: '/admin/search-configs', icon: <ManageSearchIcon /> },
  { label: 'Source Websites', path: '/admin/source-websites', icon: <PublicIcon /> },
] as const

export function Sidebar({ open }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { isStaff, isSuperuser } = useAuth()
  const width = open ? SIDEBAR_WIDTH_EXPANDED : SIDEBAR_WIDTH_COLLAPSED
  const isAdmin = isStaff || isSuperuser

  function renderItem(label: string, path: string, icon: React.ReactNode) {
    const active = location.pathname.startsWith(path)
    return (
      <Tooltip key={path} title={open ? '' : label} placement="right">
        <ListItemButton
          selected={active}
          onClick={() => navigate(path)}
          sx={{ justifyContent: open ? 'initial' : 'center', px: 2 }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: open ? 2 : 'auto',
              justifyContent: 'center',
              color: active ? 'primary.main' : 'inherit',
            }}
          >
            {icon}
          </ListItemIcon>
          {open && <ListItemText primary={label} />}
        </ListItemButton>
      </Tooltip>
    )
  }

  return (
    <Drawer
      variant="permanent"
      sx={{
        width,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width,
          boxSizing: 'border-box',
          overflowX: 'hidden',
          transition: 'width 0.2s ease',
          mt: '64px',
        },
      }}
    >
      <List>
        {USER_ITEMS.map(({ label, path, icon }) => renderItem(label, path, icon))}
      </List>

      {isAdmin && (
        <>
          <Divider />
          <List
            subheader={
              open ? (
                <ListSubheader component="div" sx={{ lineHeight: '36px' }}>
                  Admin
                </ListSubheader>
              ) : undefined
            }
          >
            {ADMIN_ITEMS.map(({ label, path, icon }) =>
              renderItem(label, path, icon),
            )}
          </List>
        </>
      )}
    </Drawer>
  )
}
