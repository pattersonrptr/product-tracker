/**
 * Collapsible navigation sidebar.
 */

import CategoryIcon from '@mui/icons-material/Category'
import HomeIcon from '@mui/icons-material/Home'
import ManageSearchIcon from '@mui/icons-material/ManageSearch'
import PeopleIcon from '@mui/icons-material/People'
import PublicIcon from '@mui/icons-material/Public'
import Drawer from '@mui/material/Drawer'
import List from '@mui/material/List'
import ListItemButton from '@mui/material/ListItemButton'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Tooltip from '@mui/material/Tooltip'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'

export const SIDEBAR_WIDTH_EXPANDED = 220
export const SIDEBAR_WIDTH_COLLAPSED = 60

interface SidebarProps {
  open: boolean
}

const NAV_ITEMS = [
  { label: 'Products', path: '/products', icon: <HomeIcon /> },
  { label: 'Search Configs', path: '/search-configs', icon: <ManageSearchIcon /> },
  { label: 'Source Websites', path: '/source-websites', icon: <PublicIcon /> },
] as const

const ADMIN_ITEMS = [
  { label: 'Users', path: '/users', icon: <PeopleIcon /> },
] as const

export function Sidebar({ open }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { isStaff, isSuperuser } = useAuth()
  const width = open ? SIDEBAR_WIDTH_EXPANDED : SIDEBAR_WIDTH_COLLAPSED
  const canManageUsers = isStaff || isSuperuser

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
        {NAV_ITEMS.map(({ label, path, icon }) => renderItem(label, path, icon))}
      </List>

      {canManageUsers && (
        <List sx={{ position: 'absolute', bottom: 8, width: '100%' }}>
          {ADMIN_ITEMS.map(({ label, path, icon }) => renderItem(label, path, icon))}
          <Tooltip title={open ? '' : 'Admin'} placement="right">
            <ListItemButton
              onClick={() => navigate('/admin')}
              sx={{ justifyContent: open ? 'initial' : 'center', px: 2 }}
            >
              <ListItemIcon sx={{ minWidth: 0, mr: open ? 2 : 'auto', justifyContent: 'center' }}>
                <CategoryIcon />
              </ListItemIcon>
              {open && <ListItemText primary="Admin" />}
            </ListItemButton>
          </Tooltip>
        </List>
      )}
    </Drawer>
  )
}
