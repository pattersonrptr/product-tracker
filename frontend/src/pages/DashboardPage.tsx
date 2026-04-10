/**
 * Dashboard page — user landing page after login.
 *
 * Shows:
 *  - Active Alerts card with count and quick link
 *  - Recent Opportunities card (products below target price)
 *  - Next Checks card (when each alert is scheduled to run)
 */

import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive'
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart'
import ScheduleIcon from '@mui/icons-material/Schedule'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardContent from '@mui/material/CardContent'
import CardHeader from '@mui/material/CardHeader'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Divider from '@mui/material/Divider'
import Grid from '@mui/material/Grid'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import ListItemText from '@mui/material/ListItemText'
import Typography from '@mui/material/Typography'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '@/components/common/PageHeader'
import { useAuth } from '@/context/AuthContext'
import { useDashboardSummary } from '@/hooks/useDashboardSummary'
import { formatCurrency } from '@/lib/formatters'

export function DashboardPage() {
  const navigate = useNavigate()
  const { userId, username } = useAuth()
  const { summary, loading, error } = useDashboardSummary(userId)

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={6}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <PageHeader title={`Welcome back${username ? `, ${username}` : ''}!`} />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* ── Active Alerts card ──────────────────────────────────── */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card>
            <CardHeader
              avatar={<NotificationsActiveIcon color="primary" />}
              title="Active Alerts"
            />
            <CardContent>
              <Typography variant="h3" fontWeight="bold" color="primary">
                {summary?.activeAlertsCount ?? 0}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                price alerts currently monitoring
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/alerts')}
              >
                Manage Alerts
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* ── Recent Opportunities card ────────────────────────────── */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<ShoppingCartIcon color="success" />}
              title="Recent Opportunities"
            />
            <CardContent>
              {!summary || summary.recentOpportunities.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No products below target price found yet.
                </Typography>
              ) : (
                <List dense disablePadding>
                  {summary.recentOpportunities.map(({ product, alert }) => (
                    <Box key={product.id}>
                      <ListItem
                        disableGutters
                        secondaryAction={
                          <Chip
                            label={`🎯 ${formatCurrency(product.currentPrice!)}`}
                            color="success"
                            size="small"
                          />
                        }
                      >
                        <ListItemText
                          primary={
                            <Typography
                              variant="body2"
                              noWrap
                              sx={{
                                maxWidth: 160,
                                cursor: 'pointer',
                                '&:hover': { textDecoration: 'underline' },
                              }}
                              onClick={() => navigate(`/products/${product.id}`)}
                            >
                              {product.title}
                            </Typography>
                          }
                          secondary={`Target: ${formatCurrency(alert.maxPrice)}`}
                        />
                      </ListItem>
                      <Divider component="li" />
                    </Box>
                  ))}
                </List>
              )}
              <Button
                variant="outlined"
                size="small"
                sx={{ mt: 2 }}
                onClick={() => navigate('/products')}
              >
                View Products
              </Button>
            </CardContent>
          </Card>
        </Grid>

        {/* ── Next Checks card ─────────────────────────────────────── */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ height: '100%' }}>
            <CardHeader
              avatar={<ScheduleIcon color="info" />}
              title="Next Checks"
            />
            <CardContent>
              {!summary || summary.nextChecks.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No active alerts scheduled.
                </Typography>
              ) : (
                <List dense disablePadding>
                  {summary.nextChecks.map((check) => (
                    <Box key={check.alertId}>
                      <ListItem disableGutters>
                        <ListItemText
                          primary={
                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                              {check.searchTerm}
                            </Typography>
                          }
                          secondary={`Next: ${new Date(check.nextCheckAt).toLocaleString()}`}
                        />
                      </ListItem>
                      <Divider component="li" />
                    </Box>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
