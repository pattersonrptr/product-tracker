/**
 * Application footer.
 */

import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        py: 2,
        px: 3,
        mt: 'auto',
        borderTop: 1,
        borderColor: 'divider',
        textAlign: 'center',
      }}
    >
      <Typography variant="body2" color="text.secondary">
        Product Tracker © {new Date().getFullYear()}
      </Typography>
    </Box>
  )
}
