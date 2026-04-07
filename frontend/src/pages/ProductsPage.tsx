/**
 * Products list page — MUI DataGrid with server-side pagination, sort, filters,
 * bulk delete, and an inline edit modal.
 */

import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import FilterListIcon from '@mui/icons-material/FilterList'
import VisibilityIcon from '@mui/icons-material/Visibility'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import Collapse from '@mui/material/Collapse'
import FormControl from '@mui/material/FormControl'
import IconButton from '@mui/material/IconButton'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import Select from '@mui/material/Select'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Tooltip from '@mui/material/Tooltip'
import {
  DataGrid,
  type GridColDef,
  type GridSortModel,
  type GridPaginationModel,
  type GridRowSelectionModel,
} from '@mui/x-data-grid'
import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSnackbar } from 'notistack'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'
import { GenericFormModal } from '@/components/common/GenericFormModal'
import { PageHeader } from '@/components/common/PageHeader'
import { usePaginatedResource } from '@/hooks/usePaginatedResource'
import { formatCurrency } from '@/lib/formatters'
import { logger } from '@/lib/logger'
import { deleteProduct, getProducts, updateProduct } from '@/services/productService'
import type { Product, ProductCondition, ProductUpdatePayload } from '@/types/product'

// ---------------------------------------------------------------------------
// Filter state
// ---------------------------------------------------------------------------

interface Filters {
  title: string
  condition: string
  isAvailable: string
}

const defaultFilters: Filters = { title: '', condition: '', isAvailable: '' }

// ---------------------------------------------------------------------------
// Edit form state
// ---------------------------------------------------------------------------

interface EditFormState {
  title: string
  url: string
  condition: ProductCondition
  isAvailable: boolean
  description: string
  sellerName: string
}

const CONDITIONS: ProductCondition[] = ['new', 'used', 'refurbished', 'undetermined']

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ProductsPage() {
  const navigate = useNavigate()
  const { enqueueSnackbar } = useSnackbar()

  const [paginationModel, setPaginationModel] = useState<GridPaginationModel>({
    page: 0,
    pageSize: 10,
  })
  const [sortModel, setSortModel] = useState<GridSortModel>([])
  const [filters, setFilters] = useState<Filters>(defaultFilters)
  const [showFilters, setShowFilters] = useState(false)
  const [rowSelection, setRowSelection] = useState<GridRowSelectionModel>({
    type: 'include',
    ids: new Set(),
  })

  // Single delete
  const [deleteId, setDeleteId] = useState<string | null>(null)
  // Bulk delete
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)

  // Edit modal
  const [editProduct, setEditProduct] = useState<Product | null>(null)
  const [editForm, setEditForm] = useState<EditFormState>({
    title: '',
    url: '',
    condition: 'undetermined',
    isAvailable: true,
    description: '',
    sellerName: '',
  })
  const [saving, setSaving] = useState(false)

  // ---------------------------------------------------------------------------
  // Data fetching
  // ---------------------------------------------------------------------------

  const fetcher = useCallback(
    () =>
      getProducts({
        limit: paginationModel.pageSize,
        offset: paginationModel.page * paginationModel.pageSize,
        sort_by: sortModel[0]?.field,
        sort_order: sortModel[0]?.sort ?? undefined,
        ...(filters.title ? { title: filters.title } : {}),
        ...(filters.condition ? { condition: filters.condition } : {}),
        ...(filters.isAvailable !== ''
          ? { is_available: filters.isAvailable === 'true' }
          : {}),
      }),
    [paginationModel, sortModel, filters],
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

  function openEdit(product: Product) {
    setEditProduct(product)
    setEditForm({
      title: product.title,
      url: product.url,
      condition: product.condition,
      isAvailable: product.isAvailable,
      description: product.description ?? '',
      sellerName: product.sellerName ?? '',
    })
  }

  function applyFilters(next: Partial<Filters>) {
    setFilters((prev) => ({ ...prev, ...next }))
    setPaginationModel((prev) => ({ ...prev, page: 0 }))
  }

  // ---------------------------------------------------------------------------
  // Handlers
  // ---------------------------------------------------------------------------

  async function handleDelete() {
    if (!deleteId) return
    try {
      await deleteProduct(deleteId)
      enqueueSnackbar('Product deleted', { variant: 'success' })
      reload()
    } catch (err) {
      logger.error('Failed to delete product', { id: deleteId }, err)
      enqueueSnackbar('Failed to delete product', { variant: 'error' })
    } finally {
      setDeleteId(null)
    }
  }

  async function handleBulkDelete() {
    setBulkDeleteOpen(false)
    const ids = selectedIds()
    try {
      await Promise.all(ids.map(deleteProduct))
      enqueueSnackbar(`${ids.length} product(s) deleted`, { variant: 'success' })
      setRowSelection({ type: 'include', ids: new Set() })
      reload()
    } catch (err) {
      logger.error('Failed to bulk delete products', { ids }, err)
      enqueueSnackbar('Failed to delete some products', { variant: 'error' })
    }
  }

  async function handleEdit() {
    if (!editProduct) return
    setSaving(true)
    try {
      const payload: ProductUpdatePayload = {
        title: editForm.title || undefined,
        url: editForm.url || undefined,
        condition: editForm.condition,
        isAvailable: editForm.isAvailable,
        description: editForm.description || undefined,
        sellerName: editForm.sellerName || undefined,
      }
      await updateProduct(editProduct.id, payload)
      enqueueSnackbar('Product updated', { variant: 'success' })
      setEditProduct(null)
      reload()
    } catch (err) {
      logger.error('Failed to update product', { id: editProduct.id }, err)
      enqueueSnackbar('Failed to update product', { variant: 'error' })
    } finally {
      setSaving(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Columns
  // ---------------------------------------------------------------------------

  const columns: GridColDef<Product>[] = [
    { field: 'title', headerName: 'Title', flex: 2, minWidth: 200 },
    {
      field: 'currentPrice',
      headerName: 'Current Price',
      width: 140,
      valueFormatter: (value: number | undefined) =>
        value != null ? formatCurrency(value) : '—',
    },
    { field: 'condition', headerName: 'Condition', width: 130 },
    {
      field: 'isAvailable',
      headerName: 'Available',
      width: 110,
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
      width: 120,
      getActions: ({ row }) => [
        <Tooltip title="View details" key="view">
          <IconButton size="small" onClick={() => navigate(`/products/${row.id}`)}>
            <VisibilityIcon fontSize="small" />
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
  // Render
  // ---------------------------------------------------------------------------

  return (
    <Box>
      <PageHeader title="Products" />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* ── Toolbar ──────────────────────────────────────────────────── */}
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} alignItems="center">
        <Button
          variant={showFilters ? 'contained' : 'outlined'}
          startIcon={<FilterListIcon />}
          onClick={() => setShowFilters((v) => !v)}
          size="small"
        >
          Filters
        </Button>
        {selectionCount() > 0 && (
          <Button
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            size="small"
            onClick={() => setBulkDeleteOpen(true)}
          >
            Delete selected ({selectionCount()})
          </Button>
        )}
      </Stack>

      {/* ── Filter toolbar ────────────────────────────────────────────── */}
      <Collapse in={showFilters}>
        <Stack direction="row" spacing={2} sx={{ mb: 2 }} flexWrap="wrap">
          <TextField
            label="Title"
            size="small"
            value={filters.title}
            onChange={(e) => applyFilters({ title: e.target.value })}
            sx={{ minWidth: 200 }}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Condition</InputLabel>
            <Select
              label="Condition"
              value={filters.condition}
              onChange={(e) => applyFilters({ condition: e.target.value })}
            >
              <MenuItem value="">All</MenuItem>
              {CONDITIONS.map((c) => (
                <MenuItem key={c} value={c}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Available</InputLabel>
            <Select
              label="Available"
              value={filters.isAvailable}
              onChange={(e) => applyFilters({ isAvailable: e.target.value })}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
          <Button
            size="small"
            onClick={() => {
              setFilters(defaultFilters)
              setPaginationModel((prev) => ({ ...prev, page: 0 }))
            }}
          >
            Clear
          </Button>
        </Stack>
      </Collapse>

      {/* ── Data grid ────────────────────────────────────────────────── */}
      <DataGrid
        rows={items}
        columns={columns}
        rowCount={total}
        loading={loading}
        paginationMode="server"
        sortingMode="server"
        paginationModel={paginationModel}
        onPaginationModelChange={setPaginationModel}
        sortModel={sortModel}
        onSortModelChange={setSortModel}
        pageSizeOptions={[10, 25, 50, 100]}
        checkboxSelection
        rowSelectionModel={rowSelection}
        onRowSelectionModelChange={setRowSelection}
        disableRowSelectionOnClick
        autoHeight
      />

      {/* ── Edit modal ───────────────────────────────────────────────── */}
      <GenericFormModal
        open={editProduct !== null}
        title={`Edit Product — ${editProduct?.title ?? ''}`}
        onClose={() => setEditProduct(null)}
        onSave={handleEdit}
        saving={saving}
      >
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField
            label="Title"
            value={editForm.title}
            onChange={(e) => setEditForm((f) => ({ ...f, title: e.target.value }))}
            fullWidth
            size="small"
          />
          <TextField
            label="URL"
            value={editForm.url}
            onChange={(e) => setEditForm((f) => ({ ...f, url: e.target.value }))}
            fullWidth
            size="small"
          />
          <FormControl size="small" fullWidth>
            <InputLabel>Condition</InputLabel>
            <Select
              label="Condition"
              value={editForm.condition}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, condition: e.target.value as ProductCondition }))
              }
            >
              {CONDITIONS.map((c) => (
                <MenuItem key={c} value={c}>
                  {c.charAt(0).toUpperCase() + c.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl size="small" fullWidth>
            <InputLabel>Available</InputLabel>
            <Select
              label="Available"
              value={editForm.isAvailable ? 'true' : 'false'}
              onChange={(e) =>
                setEditForm((f) => ({ ...f, isAvailable: e.target.value === 'true' }))
              }
            >
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Seller Name"
            value={editForm.sellerName}
            onChange={(e) => setEditForm((f) => ({ ...f, sellerName: e.target.value }))}
            fullWidth
            size="small"
          />
          <TextField
            label="Description"
            value={editForm.description}
            onChange={(e) => setEditForm((f) => ({ ...f, description: e.target.value }))}
            fullWidth
            multiline
            rows={3}
            size="small"
          />
        </Stack>
      </GenericFormModal>

      {/* ── Single delete confirmation ────────────────────────────────── */}
      <ConfirmationDialog
        open={!!deleteId}
        title="Delete Product"
        message="Are you sure you want to delete this product? This action cannot be undone."
        confirmLabel="Delete"
        onConfirm={handleDelete}
        onCancel={() => setDeleteId(null)}
      />

      {/* ── Bulk delete confirmation ──────────────────────────────────── */}
      <ConfirmationDialog
        open={bulkDeleteOpen}
        title="Delete Products"
        message={`Are you sure you want to delete ${selectionCount()} product(s)? This action cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleBulkDelete}
        onCancel={() => setBulkDeleteOpen(false)}
      />
    </Box>
  )
}
