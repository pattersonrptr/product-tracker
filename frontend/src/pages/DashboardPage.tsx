/**
 * Dashboard page — landing page after login.
 *
 * Cards:
 *   1. Active Alerts — count + quick link to /alerts
 *   2. Recent Opportunities — products below target price
 *   3. Next Checks — when each alert is scheduled to run
 */

import AccessTimeIcon from '@mui/icons-material/AccessTime'
import LocalOfferIcon from '@mui/icons-material/LocalOffer'
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import IconButton from '@mui/material/IconButton'
import Link from '@mui/material/Link'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemIcon from '@mui/material/ListItemIcon'
import ListItemText from '@mui/material/ListItemText'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/context/AuthContext'
import { useDashboardSummary } from '@/hooks/useDashboardSummary'
import { formatCurrency, formatDateTime } from '@/lib/formatters'
import type { OpportunityProduct, AlertNextCheck } from '@/services/dashboardService'

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ActiveAlertsCard({
  active,
  total,
}: {
  active: number
  total: number
}) {
  const navigate = useNavigate()

  return (
    <Card
      sx={{
        cursor: 'pointer',
        transition: 'box-shadow 0.2s',
        '&:hover': { boxShadow: 6 },
      }}
      onClick={() => navigate('/alerts')}
    >
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <NotificationsActiveIcon color="primary" />
          <Typography variant="h6">Active Alerts</Typography>
        </Stack>
        <Typography variant="h3" fontWeight="bold" color="primary">
          {active}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {total} total alert{total !== 1 ? 's' : ''} configured
        </Typography>
      </CardContent>
    </Card>
  )
}

function OpportunitiesCard({
  opportunities,
}: {
  opportunities: OpportunityProduct[]
}) {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <TrendingDownIcon color="success" />
          <Typography variant="h6">Recent Opportunities</Typography>
          <Chip
            size="small"
            label={opportunities.length}
            color="success"
            variant="outlined"
          />
        </Stack>

        {opportunities.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            No opportunities found yet. Create alerts to start tracking prices!
          </Typography>
        ) : (
          <List dense disablePadding>
            {opportunities.slice(0, 8).map((op) => (
              <ListItem
                key={`${op.alertId}-${op.id}`}
                disableGutters
                secondaryAction={
                  <Tooltip title="Open product">
                    <IconButton
                      edge="end"
                      size="small"
                      component="a"
                      href={op.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                }
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <LocalOfferIcon fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                      {op.title}
                    </Typography>
                  }
                  secondary={
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography
                        component="span"
                        variant="body2"
                        fontWeight="bold"
                        color="success.main"
                      >
                        {formatCurrency(op.currentPrice)}
                      </Typography>
                      <Typography
                        component="span"
                        variant="caption"
                        color="text.secondary"
                      >
                        (max: {formatCurrency(op.alertMaxPrice)})
                      </Typography>
                      <Chip
                        size="small"
                        label={op.alertSearchTerm}
                        variant="outlined"
                        sx={{ height: 20, fontSize: '0.7rem' }}
                      />
                    </Stack>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}

function NextChecksCard({ checks }: { checks: AlertNextCheck[] }) {
  return (
    <Card>
      <CardContent>
        <Stack direction="row" alignItems="center" spacing={1} mb={1}>
          <AccessTimeIcon color="info" />
          <Typography variant="h6">Next Checks</Typography>
        </Stack>

        {checks.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            No active alerts scheduled.
          </Typography>
        ) : (
          <List dense disablePadding>
            {checks.slice(0, 8).map((check) => (
              <ListItem key={check.alertId} disableGutters>
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <AccessTimeIcon fontSize="small" color="info" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight="medium">
                      {check.searchTerm}
                    </Typography>
                  }
                  secondary={
                    check.nextCheckAt ? (
                      <Typography variant="caption" color="text.secondary">
                        Next: {formatDateTime(check.nextCheckAt)} (every{' '}
                        {check.frequencyMinutes} min)
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        Every {check.frequencyMinutes} min — not yet triggered
                      </Typography>
                    )
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function DashboardPage() {
  const { userId } = useAuth()
  const { summary, loading, error } = useDashboardSummary(userId)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={300}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box>
        <PageHeader title="Dashboard" />
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      </Box>
    )
  }

  if (!summary) {
    return (
      <Box>
        <PageHeader title="Dashboard" />
        <Typography color="text.secondary">No data available.</Typography>
      </Box>
    )
  }

  return (
    <Box>
      <PageHeader title="Dashboard" />
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2, mt: -2 }}>
        Your price tracking overview
      </Typography>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            md: '1fr 1fr',
            lg: '300px 1fr 1fr',
          },
          gap: 3,
          mt: 2,
        }}
      >
        {/* Active Alerts card */}
        <ActiveAlertsCard
          active={summary.activeAlerts}
          total={summary.totalAlerts}
        />

        {/* Recent Opportunities */}
        <OpportunitiesCard opportunities={summary.recentOpportunities} />

        {/* Next Checks */}
        <NextChecksCard checks={summary.nextChecks} />
      </Box>

      <Divider sx={{ my: 4 }} />

      <Typography variant="body2" color="text.secondary">
        Tip: Create{' '}
        <Link href="/alerts" variant="body2">
          price alerts
        </Link>{' '}
        to get notified when products drop below your target price.
      </Typography>
    </Box>
  )
}
