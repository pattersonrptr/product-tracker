/**
 * Main application layout — renders the persistent shell (Header, Sidebar, Footer)
 * and the routed page content in between.
 */

import Box from '@mui/material/Box'
import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Footer } from './Footer'
import { Header } from './Header'
import { Sidebar, SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_WIDTH_EXPANDED } from './Sidebar'

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const sidebarWidth = sidebarOpen
    ? SIDEBAR_WIDTH_EXPANDED
    : SIDEBAR_WIDTH_COLLAPSED

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header
        onMenuClick={() => setSidebarOpen((prev) => !prev)}
        sidebarOpen={sidebarOpen}
      />

      <Box sx={{ display: 'flex', flex: 1, mt: '64px' }}>
        <Sidebar open={sidebarOpen} />

        <Box
          component="main"
          sx={{
            flex: 1,
            ml: `${sidebarWidth}px`,
            transition: 'margin-left 0.2s ease',
            p: 3,
            minWidth: 0,
          }}
        >
          <Outlet />
        </Box>
      </Box>

      <Box sx={{ ml: `${sidebarWidth}px`, transition: 'margin-left 0.2s ease' }}>
        <Footer />
      </Box>
    </Box>
  )
}
