/**
 * Top navigation bar.
 */

import MenuIcon from '@mui/icons-material/Menu'
import AppBar from '@mui/material/AppBar'
import IconButton from '@mui/material/IconButton'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'

interface HeaderProps {
  onMenuClick: () => void
  sidebarOpen: boolean
}

export function Header({ onMenuClick }: HeaderProps) {
  const { logout } = useAuth()
  const [confirmOpen, setConfirmOpen] = useState(false)

  return (
    <>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={onMenuClick}
            sx={{ mr: 2 }}
            aria-label="toggle sidebar"
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Product Tracker
          </Typography>

          <Button color="inherit" onClick={() => setConfirmOpen(true)}>
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      <ConfirmationDialog
        open={confirmOpen}
        title="Sign out"
        message="Are you sure you want to sign out?"
        confirmLabel="Sign out"
        cancelLabel="Stay"
        onConfirm={() => { setConfirmOpen(false); logout() }}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  )
}
