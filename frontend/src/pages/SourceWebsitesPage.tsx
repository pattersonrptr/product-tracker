/**
 * Source websites page — full CRUD with create/edit modals and bulk delete.
 */

import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import FormControlLabel from '@mui/material/FormControlLabel'
import IconButton from '@mui/material/IconButton'
import Link from '@mui/material/Link'
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
import { useCallback, useState } from 'react'
import { useSnackbar } from 'notistack'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'
import { GenericFormModal } from '@/components/common/GenericFormModal'
import { PageHeader } from '@/components/common/PageHeader'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import { logger } from '@/lib/logger'
import {
  createSourceWebsite,
  deleteSourceWebsite,
  getSourceWebsites,
  updateSourceWebsite,
} from '@/services/sourceWebsiteService'
import type {
  SourceWebsite,
  SourceWebsiteCreatePayload,
  SourceWebsiteUpdatePayload,
} from '@/types/sourceWebsite'

// ---------------------------------------------------------------------------
// Form state
// ---------------------------------------------------------------------------

interface FormState {
  name: string
  baseUrl: string
  isActive: boolean
}

const defaultForm: FormState = { name: '', baseUrl: '', isActive: true }

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function SourceWebsitesPage() {
  const { enqueueSnackbar } = useSnackbar()

  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10,
  })
  const [rowSelection, setRowSelection] = useState<GridRowSelectionModel>({
    type: 'include',
    ids: new Set(),
  })
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  // Create modal
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<FormState>(defaultForm)
  const [creating, setCreating] = useState(false)

  // Edit modal
  const [editSite, setEditSite] = useState<SourceWebsite | null>(null)
  const [editForm, setEditForm] = useState<FormState>(defaultForm)
  const [saving, setSaving] = useState(false)

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetcher = useCallback(
    () =>
      getSourceWebsites({
        limit: paginationModel.pageSize,
        offset: paginationModel.page * paginationModel.pageSize,
      }),
    [paginationModel],
  )

  const { items, total, loading, error, reload } = usePaginatedResource(fetcher)

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  function selectedIds(): string[] {
    if (rowSelection.type !== 'include') return []
    return Array.from(rowSelection.ids) as string[]
  }

  function selectionCount(): number {
    return rowSelection.type === 'include' ? rowSelection.ids.size : 0
  }

  function openEdit(site: SourceWebsite) {
    setEditSite(site)
    setEditForm({ name: site.name, baseUrl: site.baseUrl, isActive: site.isActive })
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function handleCreate() {
    if (!createForm.name || !createForm.baseUrl) {
      enqueueSnackbar('Name and Base URL are required', { variant: 'warning' })
      return
    }
    setCreating(true)
    try {
      const payload: SourceWebsiteCreatePayload = {
        name: createForm.name,
        baseUrl: createForm.baseUrl,
        isActive: createForm.isActive,
      }
      await createSourceWebsite(payload)
      enqueueSnackbar('Source website created', { variant: 'success' })
      setCreateOpen(false)
      setCreateForm(defaultForm)
      reload()
    } catch (err) {
      logger.error('Failed to create source website', { name: createForm.name }, err)
      enqueueSnackbar('Failed to create source website', { variant: 'error' })
    } finally {
      setCreating(false)
    }
  }

  async function handleEdit() {
    if (!editSite) return
    setSaving(true)
    try {
      const payload: SourceWebsiteUpdatePayload = {
        name: editForm.name || undefined,
        baseUrl: editForm.baseUrl || undefined,
        isActive: editForm.isActive,
      }
      await updateSourceWebsite(editSite.id, payload)
      enqueueSnackbar('Source website updated', { variant: 'success' })
      setEditSite(null)
      reload()
    } catch (err) {
      logger.error('Failed to update source website', { id: editSite.id }, err)
      enqueueSnackbar('Failed to update source website', { variant: 'error' })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!deleteId) return
    try {
      await deleteSourceWebsite(deleteId)
      enqueueSnackbar('Source website deleted', { variant: 'success' })
      reload()
    } catch (err) {
      logger.error('Failed to delete source website', { id: deleteId }, err)
      enqueueSnackbar('Failed to delete source website', { variant: 'error' })
    } finally {
      setDeleteId(null)
    }
  }

  async function handleBulkDelete() {
    setBulkDeleteOpen(false)
    const ids = selectedIds()
    try {
      await Promise.all(ids.map(deleteSourceWebsite))
      enqueueSnackbar(`${ids.length} website(s) deleted`, { variant: 'success' })
      setRowSelection({ type: 'include', ids: new Set() })
      reload()
    } catch (err) {
      logger.error('Failed to bulk delete source websites', { ids }, err)
      enqueueSnackbar('Failed to delete some websites', { variant: 'error' })
    }
  }

  // ---------------------------------------------------------------------------
  // Shared form fields renderer
  // ---------------------------------------------------------------------------

  function renderFormFields(form: FormState, setForm: React.Dispatch<React.SetStateAction<FormState>>) {
    return (
      <Stack spacing={2} sx={{ pt: 1 }}>
        <TextField
          label="Name"
          value={form.name}
          onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          required
          fullWidth
          size="small"
        />
        <TextField
          label="Base URL"
          value={form.baseUrl}
          onChange={(e) => setForm((f) => ({ ...f, baseUrl: e.target.value }))}
          required
          fullWidth
          size="small"
          placeholder="https://example.com"
        />
        <FormControlLabel
          control={
            <Switch
              checked={form.isActive}
              onChange={(e) => setForm((f) => ({ ...f, isActive: e.target.checked }))}
            />
          }
          label="Active"
        />
      </Stack>
    )
  }

  // ---------------------------------------------------------------------------
  // Columns
  // ---------------------------------------------------------------------------

  const columns: GridColDef<SourceWebsite>[] = [
    { field: 'name', headerName: 'Name', flex: 1, minWidth: 150 },
    {
      field: 'baseUrl',
      headerName: 'Base URL',
      flex: 2,
      minWidth: 200,
      renderCell: ({ value }) => (
        <Link href={value} target="_blank" rel="noopener noreferrer">
          {value}
        </Link>
      ),
    },
    {
      field: 'isActive',
      headerName: 'Active',
      width: 100,
      renderCell: ({ value }) => (
        <Chip
          label={value ? 'Yes' : 'No'}
          color={value ? 'success' : 'default'}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      type: 'actions',
      headerName: 'Actions',
      width: 100,
      getActions: ({ row }) => [
        <Tooltip title="Edit" key="edit">
          <IconButton size="small" onClick={() => openEdit(row)}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
        <Tooltip title="Delete" key="delete">
          <IconButton
            size="small"
            color="error"
            onClick={() => setDeleteId(row.id)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
      ],
    },
  ]

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box>
      <PageHeader
        title="Source Websites"
        actionLabel="Add Website"
        onAction={() => setCreateOpen(true)}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load source websites.
        </Alert>
      )}

      {selectionCount() > 0 && (
        <Box sx={{ mb: 1 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            size="small"
            onClick={() => setBulkDeleteOpen(true)}
          >
            Delete selected ({selectionCount()})
          </Button>
        </Box>
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
        checkboxSelection
        rowSelectionModel={rowSelection}
        onRowSelectionModelChange={setRowSelection}
        disableRowSelectionOnClick
        autoHeight
      />

      {/* ── Create modal ─────────────────────────────────────────────── */}
      <GenericFormModal
        open={createOpen}
        title="New Source Website"
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
        open={editSite !== null}
        title={`Edit Website — ${editSite?.name ?? ''}`}
        onClose={() => setEditSite(null)}
        onSave={handleEdit}
        saving={saving}
      >
        {renderFormFields(editForm, setEditForm)}
      </GenericFormModal>

      {/* ── Single delete confirmation ────────────────────────────────── */}
      <ConfirmationDialog
        open={deleteId !== null}
        title="Delete Source Website"
        message="Are you sure you want to delete this source website?"
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />

      {/* ── Bulk delete confirmation ──────────────────────────────────── */}
      <ConfirmationDialog
        open={bulkDeleteOpen}
        title="Delete Source Websites"
        message={`Are you sure you want to delete ${selectionCount()} website(s)?`}
        confirmLabel="Delete"
        onConfirm={handleBulkDelete}
        onCancel={() => setBulkDeleteOpen(false)}
      />
    </Box>
  )
}


