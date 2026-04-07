/**
 * Users management page.
 * Accessible to staff (read-only) and superusers (full CRUD).
 */

import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import FormControlLabel from '@mui/material/FormControlLabel'
import IconButton from '@mui/material/IconButton'
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
import { useAuth } from '@/context/AuthContext'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import { logger } from '@/lib/logger'
import {
  createUser,
  deleteUser,
  updateUser,
  getUsers,
  type UserCreatePayload,
  type UserUpdatePayload,
} from '@/services/userService'
import type { User } from '@/types/user'

// ---------------------------------------------------------------------------
// Form state helpers
// ---------------------------------------------------------------------------

interface CreateFormState {
  username: string
  email: string
  password: string
}

interface EditFormState {
  username: string
  email: string
  isActive: boolean
  isStaff: boolean
  isSuperuser: boolean
}

const defaultCreate: CreateFormState = { username: '', email: '', password: '' }
const defaultEdit: EditFormState = {
  username: '',
  email: '',
  isActive: true,
  isStaff: false,
  isSuperuser: false,
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function UsersPage() {
  const { enqueueSnackbar } = useSnackbar()
  const { isSuperuser } = useAuth()

  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10,
  })
  const [rowSelection, setRowSelection] = useState<GridRowSelectionModel>({
    type: 'include',
    ids: new Set(),
  })

  // Single delete confirmation
  const [deleteId, setDeleteId] = useState<string | null>(null)
  // Bulk delete confirmation
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  // Create modal
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState<CreateFormState>(defaultCreate)
  const [creating, setCreating] = useState(false)

  // Edit modal
  const [editUser, setEditUser] = useState<User | null>(null)
  const [editForm, setEditForm] = useState<EditFormState>(defaultEdit)
  const [saving, setSaving] = useState(false)

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetcher = useCallback(
    () =>
      getUsers({
        limit: paginationModel.pageSize,
        offset: paginationModel.page * paginationModel.pageSize,
      }),
    [paginationModel],
  )

  const { items, total, loading, error, reload } = usePaginatedResource(fetcher)

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  /** IDs currently selected (only valid for 'include' type). */
  function selectedIds(): string[] {
    if (rowSelection.type !== 'include') return []
    return Array.from(rowSelection.ids) as string[]
  }

  function selectionCount(): number {
    return rowSelection.type === 'include' ? rowSelection.ids.size : 0
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  function openEdit(user: User) {
    setEditUser(user)
    setEditForm({
      username: user.username,
      email: user.email,
      isActive: user.isActive,
      isStaff: user.isStaff,
      isSuperuser: user.isSuperuser,
    })
  }

  async function handleCreate() {
    if (!createForm.username || !createForm.email || !createForm.password) {
      enqueueSnackbar('All fields are required', { variant: 'warning' })
      return
    }
    setCreating(true)
    try {
      const payload: UserCreatePayload = {
        username: createForm.username,
        email: createForm.email,
        password: createForm.password,
      }
      await createUser(payload)
      enqueueSnackbar('User created', { variant: 'success' })
      setCreateOpen(false)
      setCreateForm(defaultCreate)
      reload()
    } catch (err) {
      logger.error('Failed to create user', { username: createForm.username }, err)
      enqueueSnackbar('Failed to create user', { variant: 'error' })
    } finally {
      setCreating(false)
    }
  }

  async function handleEdit() {
    if (!editUser) return
    setSaving(true)
    try {
      const payload: UserUpdatePayload = {
        username: editForm.username || undefined,
        email: editForm.email || undefined,
        isActive: editForm.isActive,
        isStaff: editForm.isStaff,
        isSuperuser: editForm.isSuperuser,
      }
      await updateUser(editUser.id, payload)
      enqueueSnackbar('User updated', { variant: 'success' })
      setEditUser(null)
      reload()
    } catch (err) {
      logger.error('Failed to update user', { id: editUser.id }, err)
      enqueueSnackbar('Failed to update user', { variant: 'error' })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!deleteId) return
    try {
      await deleteUser(deleteId)
      enqueueSnackbar('User deleted', { variant: 'success' })
      reload()
    } catch (err) {
      logger.error('Failed to delete user', { id: deleteId }, err)
      enqueueSnackbar('Failed to delete user', { variant: 'error' })
    } finally {
      setDeleteId(null)
    }
  }

  async function handleBulkDelete() {
    setBulkDeleteOpen(false)
    const ids = selectedIds()
    try {
      await Promise.all(ids.map(deleteUser))
      enqueueSnackbar(`${ids.length} user(s) deleted`, { variant: 'success' })
      setRowSelection({ type: 'include', ids: new Set() })
      reload()
    } catch (err) {
      logger.error('Failed to bulk delete users', { ids }, err)
      enqueueSnackbar('Failed to delete some users', { variant: 'error' })
    }
  }

  // ---------------------------------------------------------------------------
  // Columns
  // ---------------------------------------------------------------------------

  const columns: GridColDef<User>[] = [
    { field: 'username', headerName: 'Username', flex: 1, minWidth: 140 },
    { field: 'email', headerName: 'Email', flex: 2, minWidth: 200 },
    {
      field: 'isActive',
      headerName: 'Active',
      width: 90,
      renderCell: ({ value }) => (
        <Chip label={value ? 'Yes' : 'No'} color={value ? 'success' : 'default'} size="small" />
      ),
    },
    {
      field: 'isStaff',
      headerName: 'Staff',
      width: 90,
      renderCell: ({ value }) => (
        <Chip label={value ? 'Yes' : 'No'} color={value ? 'info' : 'default'} size="small" />
      ),
    },
    {
      field: 'isSuperuser',
      headerName: 'Superuser',
      width: 110,
      renderCell: ({ value }) => (
        <Chip label={value ? 'Yes' : 'No'} color={value ? 'warning' : 'default'} size="small" />
      ),
    },
    {
      field: 'createdAt',
      headerName: 'Created',
      width: 170,
      valueFormatter: (value?: string) =>
        value ? new Date(value).toLocaleString() : '—',
    },
    ...(isSuperuser
      ? [
          {
            field: 'actions',
            type: 'actions' as const,
            headerName: 'Actions',
            width: 100,
            getActions: ({ row }: { row: User }) => [
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
      : []),
  ]

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box>
      <PageHeader
        title="Users"
        actionLabel={isSuperuser ? 'New User' : undefined}
        onAction={isSuperuser ? () => setCreateOpen(true) : undefined}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load users.
        </Alert>
      )}

      {isSuperuser && selectionCount() > 0 && (
        <Box sx={{ mb: 1 }}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
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
        checkboxSelection={isSuperuser}
        rowSelectionModel={rowSelection}
        onRowSelectionModelChange={setRowSelection}
        disableRowSelectionOnClick
        autoHeight
      />

      {/* ── Create modal ─────────────────────────────────────────────── */}
      <GenericFormModal
        open={createOpen}
        title="New User"
        onClose={() => {
          setCreateOpen(false)
          setCreateForm(defaultCreate)
        }}
        onSave={handleCreate}
        saving={creating}
        saveLabel="Create"
      >
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            label="Username"
            value={createForm.username}
            onChange={(e) => setCreateForm((f) => ({ ...f, username: e.target.value }))}
            required
            fullWidth
            size="small"
          />
          <TextField
            label="Email"
            type="email"
            value={createForm.email}
            onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
            required
            fullWidth
            size="small"
          />
          <TextField
            label="Password"
            type="password"
            value={createForm.password}
            onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
            required
            fullWidth
            size="small"
          />
        </Stack>
      </GenericFormModal>

      {/* ── Edit modal ───────────────────────────────────────────────── */}
      <GenericFormModal
        open={editUser !== null}
        title={`Edit User — ${editUser?.username ?? ''}`}
        onClose={() => setEditUser(null)}
        onSave={handleEdit}
        saving={saving}
      >
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            label="Username"
            value={editForm.username}
            onChange={(e) => setEditForm((f) => ({ ...f, username: e.target.value }))}
            fullWidth
            size="small"
          />
          <TextField
            label="Email"
            type="email"
            value={editForm.email}
            onChange={(e) => setEditForm((f) => ({ ...f, email: e.target.value }))}
            fullWidth
            size="small"
          />
          <FormControlLabel
            control={
              <Switch
                checked={editForm.isActive}
                onChange={(e) => setEditForm((f) => ({ ...f, isActive: e.target.checked }))}
              />
            }
            label="Active"
          />
          <FormControlLabel
            control={
              <Switch
                checked={editForm.isStaff}
                onChange={(e) => setEditForm((f) => ({ ...f, isStaff: e.target.checked }))}
              />
            }
            label="Staff"
          />
          <FormControlLabel
            control={
              <Switch
                checked={editForm.isSuperuser}
                onChange={(e) => setEditForm((f) => ({ ...f, isSuperuser: e.target.checked }))}
              />
            }
            label="Superuser"
          />
        </Stack>
      </GenericFormModal>

      {/* ── Single delete confirmation ────────────────────────────────── */}
      <ConfirmationDialog
        open={deleteId !== null}
        title="Delete User"
        message="Are you sure you want to delete this user? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />

      {/* ── Bulk delete confirmation ──────────────────────────────────── */}
      <ConfirmationDialog
        open={bulkDeleteOpen}
        title="Delete Users"
        message={`Are you sure you want to delete ${selectionCount()} user(s)? This action cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleBulkDelete}
        onCancel={() => setBulkDeleteOpen(false)}
      />
    </Box>
  )
}
