/**
 * My Alerts page — PriceAlert CRUD with DataGrid, create/edit modal,
 * pause/resume toggle, and delete.
 */

import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import PauseIcon from '@mui/icons-material/Pause'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Chip from '@mui/material/Chip'
import FormControl from '@mui/material/FormControl'
import FormControlLabel from '@mui/material/FormControlLabel'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import InputLabel from '@mui/material/InputLabel'
import ListItemText from '@mui/material/ListItemText'
import MenuItem from '@mui/material/MenuItem'
import OutlinedInput from '@mui/material/OutlinedInput'
import Select from '@mui/material/Select'
import Stack from '@mui/material/Stack'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import {
  DataGrid,
  type GridColDef,
  type GridPaginationModel,
  type GridRowSelectionModel,
} from '@mui/x-data-grid'
import { useCallback, useEffect, useState } from 'react'
import { useSnackbar } from 'notistack'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'
import { GenericFormModal } from '@/components/common/GenericFormModal'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/context/AuthContext'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import { formatCurrency, formatDateTime } from '@/lib/formatters'
import { logger } from '@/lib/logger'
import {
  createPriceAlert,
  deletePriceAlert,
  getPriceAlerts,
  updatePriceAlert,
} from '@/services/priceAlertService'
import { getAllSourceWebsites } from '@/services/sourceWebsiteService'
import type { PriceAlert, PriceAlertCreatePayload } from '@/types/priceAlert'
import type { SourceWebsite } from '@/types/sourceWebsite'

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

interface FormState {
  searchTerm: string
  maxPrice: string
  frequencyMinutes: number
  isActive: boolean
  sourceWebsiteIds: number[]
}

const defaultForm: FormState = {
  searchTerm: '',
  maxPrice: '',
  frequencyMinutes: 60,
  isActive: true,
  sourceWebsiteIds: [],
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AlertsPage() {
  const { enqueueSnackbar } = useSnackbar()
  const { userId } = useAuth()

  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10,
  })
  const [rowSelection, setRowSelection] = useState<GridRowSelectionModel>({
    type: 'include',
    ids: new Set(),
  })

  // CRUD state
  const [createOpen, setCreateOpen] = useState(false)
  const [editAlert, setEditAlert] = useState<PriceAlert | null>(null)
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [form, setForm] = useState<FormState>(defaultForm)

  // Source websites for multi-select
  const [sourceWebsites, setSourceWebsites] = useState<SourceWebsite[]>([])

  useEffect(() => {
    getAllSourceWebsites().then(setSourceWebsites).catch(() => {})
  }, [])

  // Data fetcher
  const { items, total, loading, error, setPagination, reload } =
    usePaginatedResource(getPriceAlerts)

  // Sync pagination model → hook
  useEffect(() => {
    setPagination({
      page: paginationModel.page,
      pageSize: paginationModel.pageSize,
    })
  }, [paginationModel, setPagination])

  // Open create modal
  const handleOpenCreate = useCallback(() => {
    setForm(defaultForm)
    setCreateOpen(true)
  }, [])

  // Open edit modal
  const handleOpenEdit = useCallback((alert: PriceAlert) => {
    setForm({
      searchTerm: alert.searchTerm,
      maxPrice: String(alert.maxPrice),
      frequencyMinutes: alert.frequencyMinutes,
      isActive: alert.isActive,
      sourceWebsiteIds: alert.sourceWebsiteIds,
    })
    setEditAlert(alert)
  }, [])

  // Create
  const handleCreate = useCallback(async () => {
    if (!userId) return
    try {
      const payload: PriceAlertCreatePayload = {
        searchTerm: form.searchTerm.trim(),
        maxPrice: parseFloat(form.maxPrice),
        userId,
        isActive: form.isActive,
        frequencyMinutes: form.frequencyMinutes,
        sourceWebsiteIds: form.sourceWebsiteIds,
      }
      await createPriceAlert(payload)
      enqueueSnackbar('Alert created!', { variant: 'success' })
      setCreateOpen(false)
      reload()
    } catch (err) {
      logger.error('Failed to create alert', {}, err)
      enqueueSnackbar('Failed to create alert', { variant: 'error' })
    }
  }, [form, userId, enqueueSnackbar, reload])

  // Update
  const handleUpdate = useCallback(async () => {
    if (!editAlert) return
    try {
      await updatePriceAlert(editAlert.id, {
        searchTerm: form.searchTerm.trim(),
        maxPrice: parseFloat(form.maxPrice),
        isActive: form.isActive,
        frequencyMinutes: form.frequencyMinutes,
        sourceWebsiteIds: form.sourceWebsiteIds,
      })
      enqueueSnackbar('Alert updated!', { variant: 'success' })
      setEditAlert(null)
      reload()
    } catch (err) {
      logger.error('Failed to update alert', {}, err)
      enqueueSnackbar('Failed to update alert', { variant: 'error' })
    }
  }, [editAlert, form, enqueueSnackbar, reload])

  // Toggle pause/active
  const handleToggleActive = useCallback(
    async (alert: PriceAlert) => {
      try {
        await updatePriceAlert(alert.id, { isActive: !alert.isActive })
        enqueueSnackbar(
          alert.isActive ? 'Alert paused' : 'Alert resumed',
          { variant: 'info' },
        )
        reload()
      } catch (err) {
        logger.error('Failed to toggle alert', {}, err)
        enqueueSnackbar('Failed to update alert', { variant: 'error' })
      }
    },
    [enqueueSnackbar, reload],
  )

  // Delete
  const handleDelete = useCallback(async () => {
    if (!deleteId) return
    try {
      await deletePriceAlert(deleteId)
      enqueueSnackbar('Alert deleted', { variant: 'success' })
      setDeleteId(null)
      reload()
    } catch (err) {
      logger.error('Failed to delete alert', {}, err)
      enqueueSnackbar('Failed to delete alert', { variant: 'error' })
    }
  }, [deleteId, enqueueSnackbar, reload])

  // Bulk delete
  const handleBulkDelete = useCallback(async () => {
    const ids =
      rowSelection.type === 'include'
        ? Array.from(rowSelection.ids).map(String)
        : []
    try {
      await Promise.all(ids.map(deletePriceAlert))
      enqueueSnackbar(`${ids.length} alert(s) deleted`, { variant: 'success' })
      setBulkDeleteOpen(false)
      setRowSelection({ type: 'include', ids: new Set() })
      reload()
    } catch (err) {
      logger.error('Bulk delete failed', {}, err)
      enqueueSnackbar('Some deletions failed', { variant: 'error' })
    }
  }, [rowSelection, enqueueSnackbar, reload])

  // Helper: source name by ID
  const sourceName = useCallback(
    (id: number) => sourceWebsites.find((s) => String(s.id) === String(id))?.name ?? `#${id}`,
    [sourceWebsites],
  )

  // Form fields (shared by create/edit)
  const formFields = (
    <Stack spacing={2} sx={{ mt: 1 }}>
      <TextField
        label="Search Term (keyword)"
        fullWidth
        required
        value={form.searchTerm}
        onChange={(e) => setForm((f) => ({ ...f, searchTerm: e.target.value }))}
      />
      <TextField
        label="Max Price"
        fullWidth
        required
        type="number"
        slotProps={{
          input: {
            startAdornment: (
              <InputAdornment position="start">R$</InputAdornment>
            ),
          },
        }}
        value={form.maxPrice}
        onChange={(e) => setForm((f) => ({ ...f, maxPrice: e.target.value }))}
      />
      <TextField
        label="Check Frequency (minutes)"
        fullWidth
        type="number"
        value={form.frequencyMinutes}
        onChange={(e) =>
          setForm((f) => ({
            ...f,
            frequencyMinutes: parseInt(e.target.value, 10) || 60,
          }))
        }
      />
      <FormControl fullWidth>
        <InputLabel>Source Websites</InputLabel>
        <Select
          multiple
          value={form.sourceWebsiteIds}
          onChange={(e) => {
            const val = e.target.value
            setForm((f) => ({
              ...f,
              sourceWebsiteIds:
                typeof val === 'string'
                  ? val.split(',').map(Number)
                  : (val as number[]),
            }))
          }}
          input={<OutlinedInput label="Source Websites" />}
          renderValue={(selected) =>
            selected.map((id) => sourceName(id)).join(', ')
          }
        >
          {sourceWebsites
            .filter((sw) => sw.isActive)
            .map((sw) => (
              <MenuItem key={sw.id} value={Number(sw.id)}>
                <ListItemText primary={sw.name} />
              </MenuItem>
            ))}
        </Select>
      </FormControl>
      <FormControlLabel
        control={
          <Switch
            checked={form.isActive}
            onChange={(e) =>
              setForm((f) => ({ ...f, isActive: e.target.checked }))
            }
          />
        }
        label="Active"
      />
    </Stack>
  )

  // DataGrid columns
  const columns: GridColDef<PriceAlert>[] = [
    {
      field: 'searchTerm',
      headerName: 'Keyword',
      flex: 1,
      minWidth: 150,
    },
    {
      field: 'maxPrice',
      headerName: 'Max Price',
      width: 120,
      renderCell: ({ value }) => formatCurrency(value as number),
    },
    {
      field: 'isActive',
      headerName: 'Status',
      width: 110,
      renderCell: ({ value }) => (
        <Chip
          size="small"
          label={value ? 'Active' : 'Paused'}
          color={value ? 'success' : 'default'}
        />
      ),
    },
    {
      field: 'sourceWebsiteIds',
      headerName: 'Sources',
      width: 180,
      renderCell: ({ value }) => {
        const ids = value as number[]
        if (!ids?.length) return '—'
        return (
          <Stack direction="row" spacing={0.5} flexWrap="wrap">
            {ids.map((id) => (
              <Chip
                key={id}
                size="small"
                label={sourceName(id)}
                variant="outlined"
                sx={{ height: 22, fontSize: '0.75rem' }}
              />
            ))}
          </Stack>
        )
      },
    },
    {
      field: 'frequencyMinutes',
      headerName: 'Frequency',
      width: 110,
      renderCell: ({ value }) => `${value} min`,
    },
    {
      field: 'lastTriggeredAt',
      headerName: 'Last Check',
      width: 170,
      renderCell: ({ value }) =>
        value ? formatDateTime(value as string) : 'Never',
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      sortable: false,
      filterable: false,
      renderCell: ({ row }) => (
        <Stack direction="row" spacing={0.5}>
          <Tooltip title={row.isActive ? 'Pause' : 'Resume'}>
            <IconButton
              size="small"
              onClick={() => handleToggleActive(row)}
              color={row.isActive ? 'warning' : 'success'}
            >
              {row.isActive ? <PauseIcon /> : <PlayArrowIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => handleOpenEdit(row)}>
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton
              size="small"
              color="error"
              onClick={() => setDeleteId(row.id)}
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ]

  const selectedCount =
    rowSelection.type === 'include' ? rowSelection.ids.size : 0

  return (
    <Box>
      <PageHeader
        title="My Alerts"
        actionLabel="New Alert"
        onAction={handleOpenCreate}
      />

      {selectedCount > 0 && (
        <Box sx={{ mb: 2 }}>
          <Chip
            label={`${selectedCount} selected`}
            onDelete={() =>
              setRowSelection({ type: 'include', ids: new Set() })
            }
            sx={{ mr: 1 }}
          />
          <Chip
            label="Delete selected"
            color="error"
            variant="outlined"
            onClick={() => setBulkDeleteOpen(true)}
            icon={<DeleteIcon />}
          />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <DataGrid
        rows={items}
        columns={columns}
        loading={loading}
        rowCount={total}
        paginationMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={setPaginationModel}
        pageSizeOptions={[5, 10, 25]}
        checkboxSelection
        rowSelectionModel={rowSelection}
        onRowSelectionModelChange={setRowSelection}
        disableRowSelectionOnClick
        autoHeight
        sx={{ minHeight: 400 }}
      />

      {/* Create modal */}
      <GenericFormModal
        open={createOpen}
        title="Create Alert"
        onClose={() => setCreateOpen(false)}
        onSave={handleCreate}
        saveLabel="Create"
      >
        {formFields}
      </GenericFormModal>

      {/* Edit modal */}
      <GenericFormModal
        open={!!editAlert}
        title="Edit Alert"
        onClose={() => setEditAlert(null)}
        onSave={handleUpdate}
        saveLabel="Save"
      >
        {formFields}
      </GenericFormModal>

      {/* Single delete */}
      <ConfirmationDialog
        open={!!deleteId}
        title="Delete Alert"
        message="Are you sure you want to delete this alert? This cannot be undone."
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />

      {/* Bulk delete */}
      <ConfirmationDialog
        open={bulkDeleteOpen}
        title="Delete Selected Alerts"
        message={`Delete ${selectedCount} alert(s)? This cannot be undone.`}
        onConfirm={handleBulkDelete}
        onCancel={() => setBulkDeleteOpen(false)}
      />
    </Box>
  )
}
