/**
 * My Alerts page — PriceAlert CRUD.
 *
 * Allows users to create, edit (pause/resume), and delete price alerts.
 * Each alert monitors a search term across selected source websites.
 */

import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import PauseIcon from '@mui/icons-material/Pause'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
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
import Typography from '@mui/material/Typography'
import {
  DataGrid,
  type GridColDef,
  type GridPaginationModel,
} from '@mui/x-data-grid'
import { useCallback, useEffect, useState } from 'react'
import { useSnackbar } from 'notistack'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'
import { GenericFormModal } from '@/components/common/GenericFormModal'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/context/AuthContext'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import { formatCurrency } from '@/lib/formatters'
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
  isActive: boolean
  frequencyMinutes: number
  sourceWebsiteIds: number[]
}

const defaultForm: FormState = {
  searchTerm: '',
  maxPrice: '',
  isActive: true,
  frequencyMinutes: 60,
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
  const [deleteId, setDeleteId] = useState<string | null>(null)

  // Source websites for multi-select
  const [sourceWebsites, setSourceWebsites] = useState<SourceWebsite[]>([])

  // Create modal
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<FormState>(defaultForm)
  const [creating, setCreating] = useState(false)

  // Edit modal
  const [editAlert, setEditAlert] = useState<PriceAlert | null>(null)
  const [editForm, setEditForm] = useState<FormState>(defaultForm)
  const [saving, setSaving] = useState(false)

  // ---------------------------------------------------------------------------
  // Load source websites once
  // ---------------------------------------------------------------------------

  useEffect(() => {
    getAllSourceWebsites()
      .then(setSourceWebsites)
      .catch((err) => logger.error('Failed to load source websites', {}, err))
  }, [])

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetcher = useCallback(
    () =>
      getPriceAlerts({
        limit: paginationModel.pageSize,
        offset: paginationModel.page * paginationModel.pageSize,
      }),
    [paginationModel],
  )

  const { items, total, loading, error, reload } = usePaginatedResource(fetcher)

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  function openEdit(alert: PriceAlert) {
    setEditAlert(alert)
    setEditForm({
      searchTerm: alert.searchTerm,
      maxPrice: String(alert.maxPrice),
      isActive: alert.isActive,
      frequencyMinutes: alert.frequencyMinutes,
      sourceWebsiteIds: alert.sourceWebsiteIds,
    })
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function handleCreate() {
    if (!createForm.searchTerm.trim()) {
      enqueueSnackbar('Search term is required', { variant: 'warning' })
      return
    }
    const price = parseFloat(createForm.maxPrice)
    if (isNaN(price) || price <= 0) {
      enqueueSnackbar('Max price must be a positive number', { variant: 'warning' })
      return
    }
    setCreating(true)
    try {
      const payload: PriceAlertCreatePayload = {
        searchTerm: createForm.searchTerm.trim(),
        maxPrice: price,
        isActive: createForm.isActive,
        frequencyMinutes: createForm.frequencyMinutes,
        userId: userId!,
        sourceWebsiteIds: createForm.sourceWebsiteIds,
      }
      await createPriceAlert(payload)
      enqueueSnackbar('Alert created', { variant: 'success' })
      setCreateOpen(false)
      setCreateForm(defaultForm)
      reload()
    } catch (err) {
      logger.error('Failed to create alert', { searchTerm: createForm.searchTerm }, err)
      enqueueSnackbar('Failed to create alert', { variant: 'error' })
    } finally {
      setCreating(false)
    }
  }

  async function handleEdit() {
    if (!editAlert) return
    setSaving(true)
    try {
      const price = parseFloat(editForm.maxPrice)
      await updatePriceAlert(editAlert.id, {
        searchTerm: editForm.searchTerm.trim(),
        maxPrice: isNaN(price) ? editAlert.maxPrice : price,
        isActive: editForm.isActive,
        frequencyMinutes: editForm.frequencyMinutes,
        sourceWebsiteIds: editForm.sourceWebsiteIds,
      })
      enqueueSnackbar('Alert updated', { variant: 'success' })
      setEditAlert(null)
      reload()
    } catch (err) {
      logger.error('Failed to update alert', { id: editAlert.id }, err)
      enqueueSnackbar('Failed to update alert', { variant: 'error' })
    } finally {
      setSaving(false)
    }
  }

  async function handleTogglePause(alert: PriceAlert) {
    try {
      await updatePriceAlert(alert.id, { isActive: !alert.isActive })
      enqueueSnackbar(alert.isActive ? 'Alert paused' : 'Alert resumed', {
        variant: 'success',
      })
      reload()
    } catch (err) {
      logger.error('Failed to toggle alert', { id: alert.id }, err)
      enqueueSnackbar('Failed to update alert', { variant: 'error' })
    }
  }

  async function handleDelete() {
    if (!deleteId) return
    try {
      await deletePriceAlert(deleteId)
      enqueueSnackbar('Alert deleted', { variant: 'success' })
      reload()
    } catch (err) {
      logger.error('Failed to delete alert', { id: deleteId }, err)
      enqueueSnackbar('Failed to delete alert', { variant: 'error' })
    } finally {
      setDeleteId(null)
    }
  }

  // ---------------------------------------------------------------------------
  // Columns
  // ---------------------------------------------------------------------------

  const columns: GridColDef<PriceAlert>[] = [
    { field: 'searchTerm', headerName: 'Keyword', flex: 2, minWidth: 160 },
    {
      field: 'maxPrice',
      headerName: 'Max Price',
      width: 130,
      valueFormatter: (value: number) => formatCurrency(value),
    },
    {
      field: 'isActive',
      headerName: 'Status',
      width: 120,
      renderCell: ({ value }) => (
        <Chip
          label={value ? 'Active' : 'Paused'}
          color={value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'frequencyMinutes',
      headerName: 'Frequency',
      width: 140,
      valueFormatter: (value: number) =>
        value >= 60 ? `${value / 60}h` : `${value}m`,
    },
    {
      field: 'lastTriggeredAt',
      headerName: 'Last Check',
      width: 170,
      valueFormatter: (value: string | undefined) =>
        value ? new Date(value).toLocaleString() : '—',
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 140,
      getActions: ({ row }) => [
        <Tooltip title={row.isActive ? 'Pause' : 'Resume'} key="toggle">
          <IconButton size="small" onClick={() => handleTogglePause(row)}>
            {row.isActive ? (
              <PauseIcon fontSize="small" />
            ) : (
              <PlayArrowIcon fontSize="small" />
            )}
          </IconButton>
        </Tooltip>,
        <Tooltip title="Edit" key="edit">
          <IconButton size="small" onClick={() => openEdit(row)}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
        <Tooltip title="Delete" key="delete">
          <IconButton size="small" color="error" onClick={() => setDeleteId(row.id)}>
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
      ],
    },
  ]

  // ---------------------------------------------------------------------------
  // Shared form fields renderer
  // ---------------------------------------------------------------------------

  function renderFormFields(
    form: FormState,
    setForm: React.Dispatch<React.SetStateAction<FormState>>,
  ) {
    return (
      <Stack spacing={2} sx={{ pt: 1 }}>
        <TextField
          label="Keyword / Search Term"
          value={form.searchTerm}
          onChange={(e) => setForm((f) => ({ ...f, searchTerm: e.target.value }))}
          required
          fullWidth
          size="small"
          placeholder="e.g. iPhone 15"
        />
        <TextField
          label="Max Price"
          type="number"
          value={form.maxPrice}
          onChange={(e) => setForm((f) => ({ ...f, maxPrice: e.target.value }))}
          required
          fullWidth
          size="small"
          slotProps={{
            input: {
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            },
          }}
        />
        <TextField
          label="Check Frequency (minutes)"
          type="number"
          value={form.frequencyMinutes}
          onChange={(e) =>
            setForm((f) => ({ ...f, frequencyMinutes: Number(e.target.value) }))
          }
          inputProps={{ min: 1 }}
          fullWidth
          size="small"
        />
        <FormControl fullWidth size="small">
          <InputLabel>Source Websites</InputLabel>
          <Select
            multiple
            value={form.sourceWebsiteIds}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                sourceWebsiteIds: e.target.value as number[],
              }))
            }
            input={<OutlinedInput label="Source Websites" />}
            renderValue={(selected) =>
              (selected as number[])
                .map(
                  (id) =>
                    sourceWebsites.find((s) => Number(s.id) === id)?.name ?? id,
                )
                .join(', ')
            }
          >
            {sourceWebsites.map((site) => (
              <MenuItem key={site.id} value={Number(site.id)}>
                <ListItemText primary={site.name} />
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
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box>
      <PageHeader title="My Alerts" />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load alerts.
        </Alert>
      )}

      <Box sx={{ mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          size="small"
          onClick={() => setCreateOpen(true)}
        >
          New Alert
        </Button>
      </Box>

      {!loading && items.length === 0 && !error && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          No alerts yet. Create your first alert to start monitoring prices.
        </Typography>
      )}

      <DataGrid
        rows={items}
        columns={columns}
        rowCount={total}
        loading={loading}
        paginationMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={setPaginationModel}
        pageSizeOptions={[10, 25, 50]}
        disableRowSelectionOnClick
        autoHeight
      />

      {/* ── Create modal ─────────────────────────────────────────────── */}
      <GenericFormModal
        open={createOpen}
        title="New Price Alert"
        onClose={() => {
          setCreateOpen(false)
          setCreateForm(defaultForm)
        }}
        onSave={handleCreate}
        saving={creating}
        saveLabel="Create"
      >
        {renderFormFields(createForm, setCreateForm)}
      </GenericFormModal>

      {/* ── Edit modal ───────────────────────────────────────────────── */}
      <GenericFormModal
        open={editAlert !== null}
        title={`Edit Alert — ${editAlert?.searchTerm ?? ''}`}
        onClose={() => setEditAlert(null)}
        onSave={handleEdit}
        saving={saving}
      >
        {renderFormFields(editForm, setEditForm)}
      </GenericFormModal>

      {/* ── Delete confirmation ───────────────────────────────────────── */}
      <ConfirmationDialog
        open={deleteId !== null}
        title="Delete Alert"
        message="Are you sure you want to delete this alert? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />
    </Box>
  )
}
