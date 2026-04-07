/**
 * Page header with title and optional action button.
 */

import AddIcon from '@mui/icons-material/Add'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Typography from '@mui/material/Typography'

interface PageHeaderProps {
  title: string
  actionLabel?: string
  onAction?: () => void
}

export function PageHeader({ title, actionLabel, onAction }: PageHeaderProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        mb: 3,
      }}
    >
      <Typography variant="h5" component="h1" fontWeight={600}>
        {title}
      </Typography>

      {actionLabel && onAction && (
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onAction}
        >
          {actionLabel}
        </Button>
      )}
    </Box>
  )
}
