import { useEffect, useState } from 'react'

import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import ErrorIcon from '@mui/icons-material/Error'
import GroupIcon from '@mui/icons-material/Group'
import InventoryIcon from '@mui/icons-material/Inventory'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import WebIcon from '@mui/icons-material/Web'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'

import {
  getAdminSummary,
  type AdminSummary,
  type ScraperExecution,
} from '@/services/adminService'

function StatCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string
  value: number
  subtitle?: string
  icon: React.ReactNode
}) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Box sx={{ color: 'primary.main' }}>{icon}</Box>
          <Box>
            <Typography variant="h4" fontWeight={700}>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.disabled">
                {subtitle}
              </Typography>
            )}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}

function StatusChip({ status }: { status: string }) {
  const color =
    status === 'success'
      ? 'success'
      : status === 'failed'
        ? 'error'
        : status === 'running'
          ? 'info'
          : 'default'
  return <Chip label={status} color={color} size="small" variant="outlined" />
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function AdminDashboardPage() {
  const [summary, setSummary] = useState<AdminSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAdminSummary()
      .then(setSummary)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={8}>
        <CircularProgress />
      </Box>
    )
  }

  if (!summary) {
    return (
      <Typography color="error" mt={4}>
        Erro ao carregar painel administrativo.
      </Typography>
    )
  }

  const { scraperStats, recentExecutions } = summary

  return (
    <Box>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        Painel Administrativo
      </Typography>

      {/* ── Summary cards ──────────────────────────────────────────── */}
      <Grid container spacing={3} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Usuários"
            value={summary.totalUsers}
            subtitle={`${summary.activeUsers} ativos`}
            icon={<GroupIcon fontSize="large" />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Alertas"
            value={summary.totalAlerts}
            subtitle={`${summary.activeAlerts} ativos`}
            icon={<NotificationsActiveIcon fontSize="large" />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Produtos"
            value={summary.totalProducts}
            icon={<InventoryIcon fontSize="large" />}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <StatCard
            title="Websites"
            value={summary.totalSourceWebsites}
            subtitle={`${summary.activeSourceWebsites} ativos`}
            icon={<WebIcon fontSize="large" />}
          />
        </Grid>
      </Grid>

      {/* ── Scraper stats ──────────────────────────────────────────── */}
      <Grid container spacing={3} mb={4}>
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Status dos Scrapers
            </Typography>
            <Stack direction="row" spacing={4} alignItems="center">
              <Stack alignItems="center">
                <Typography variant="h3" fontWeight={700} color="success.main">
                  {scraperStats.successCount}
                </Typography>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <CheckCircleIcon fontSize="small" color="success" />
                  <Typography variant="body2" color="text.secondary">
                    Sucesso
                  </Typography>
                </Stack>
              </Stack>
              <Stack alignItems="center">
                <Typography variant="h3" fontWeight={700} color="error.main">
                  {scraperStats.failedCount}
                </Typography>
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <ErrorIcon fontSize="small" color="error" />
                  <Typography variant="body2" color="text.secondary">
                    Falhas
                  </Typography>
                </Stack>
              </Stack>
              <Stack alignItems="center">
                <Typography variant="h3" fontWeight={700}>
                  {scraperStats.recentTotal}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total (20 últimas)
                </Typography>
              </Stack>
            </Stack>
          </Paper>
        </Grid>

        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Monitoramento
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Acompanhe workers e filas do Celery em tempo real no Flower.
            </Typography>
            <Button
              variant="outlined"
              endIcon={<OpenInNewIcon />}
              href="http://localhost:5555"
              target="_blank"
              rel="noopener"
            >
              Abrir Flower
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* ── Recent executions table ────────────────────────────────── */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Últimas Execuções
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Config ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Resultados</TableCell>
                <TableCell>Início</TableCell>
                <TableCell>Erro</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {recentExecutions.map((exec: ScraperExecution) => (
                <TableRow key={exec.id}>
                  <TableCell>{exec.id}</TableCell>
                  <TableCell>{exec.searchConfigId}</TableCell>
                  <TableCell>
                    <StatusChip status={exec.status} />
                  </TableCell>
                  <TableCell align="right">
                    {exec.resultsCount ?? '—'}
                  </TableCell>
                  <TableCell>{formatDate(exec.startedAt)}</TableCell>
                  <TableCell>
                    {exec.errorMessage ? (
                      <Typography
                        variant="caption"
                        color="error"
                        sx={{ maxWidth: 200, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis' }}
                      >
                        {exec.errorMessage}
                      </Typography>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  )
}
