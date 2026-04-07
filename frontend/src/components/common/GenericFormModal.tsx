/**
 * Generic modal wrapper used by all resource forms.
 */

import CloseIcon from '@mui/icons-material/Close'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import IconButton from '@mui/material/IconButton'

interface GenericFormModalProps {
  open: boolean
  title: string
  onClose: () => void
  onSave: () => void
  saving?: boolean
  saveLabel?: string
  children: React.ReactNode
}

export function GenericFormModal({
  open,
  title,
  onClose,
  onSave,
  saving = false,
  saveLabel = 'Save',
  children,
}: GenericFormModalProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {title}
        <IconButton onClick={onClose} size="small" aria-label="close">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers>{children}</DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          onClick={onSave}
          variant="contained"
          disabled={saving}
        >
          {saving ? 'Saving…' : saveLabel}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
