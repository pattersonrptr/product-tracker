/**
 * Plans page — pricing table showing Free, Pro, and Business tiers.
 * Users can view their current plan and subscribe/cancel.
 */

import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import StarIcon from '@mui/icons-material/Star'
import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Card from '@mui/material/Card'
import CardActions from '@mui/material/CardActions'
import CardContent from '@mui/material/CardContent'
import Chip from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { useCallback, useEffect, useState } from 'react'
import { useSnackbar } from 'notistack'
import { PageHeader } from '@/components/common/PageHeader'
import { logger } from '@/lib/logger'
import { getPlans } from '@/services/planService'
import {
  getMySubscription,
  subscribeToPlan,
  cancelSubscription,
} from '@/services/subscriptionService'
import type { Plan, Subscription } from '@/types/plan'

function formatPrice(cents: number): string {
  if (cents === 0) return 'Grátis'
  return `R$ ${(cents / 100).toFixed(2).replace('.', ',')}`
}

function formatLimit(value: number | null, suffix = ''): string {
  if (value === null) return 'Ilimitado'
  return `${value}${suffix}`
}

function formatFrequency(minutes: number): string {
  if (minutes < 60) return `${minutes} min`
  return `${minutes / 60}h`
}

interface FeatureRowProps {
  label: string
  value: string | boolean
}

function FeatureRow({ label, value }: FeatureRowProps) {
  const isBoolean = typeof value === 'boolean'
  return (
    <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ py: 0.5 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      {isBoolean ? (
        value ? (
          <CheckCircleIcon fontSize="small" color="success" />
        ) : (
          <RemoveCircleOutlineIcon fontSize="small" color="disabled" />
        )
      ) : (
        <Typography variant="body2" fontWeight={600}>
          {value}
        </Typography>
      )}
    </Stack>
  )
}

export function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { enqueueSnackbar } = useSnackbar()

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [plansData, subData] = await Promise.all([
        getPlans(),
        getMySubscription(),
      ])
      setPlans(plansData)
      setSubscription(subData)
    } catch (err) {
      logger.error('Failed to load plans', {}, err)
      setError('Erro ao carregar planos. Tente novamente.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleSubscribe = async (planId: string) => {
    try {
      setActionLoading(planId)
      const newSub = await subscribeToPlan(planId)
      setSubscription(newSub)
      enqueueSnackbar('Plano atualizado com sucesso!', { variant: 'success' })
    } catch (err) {
      logger.error('Failed to subscribe', {}, err)
      enqueueSnackbar('Erro ao assinar plano. Tente novamente.', {
        variant: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleCancel = async () => {
    try {
      setActionLoading('cancel')
      const updated = await cancelSubscription()
      setSubscription(updated)
      enqueueSnackbar('Assinatura cancelada.', { variant: 'info' })
    } catch (err) {
      logger.error('Failed to cancel subscription', {}, err)
      enqueueSnackbar('Erro ao cancelar assinatura. Tente novamente.', {
        variant: 'error',
      })
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  const currentPlanName = subscription?.planName ?? 'free'

  return (
    <Box p={3}>
      <PageHeader
        title="Planos"
        subtitle="Escolha o plano ideal para monitorar seus preços"
      />

      {subscription && subscription.planName !== 'free' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Você está no plano <strong>{subscription.planName.charAt(0).toUpperCase() + subscription.planName.slice(1)}</strong>
          {subscription.status === 'active' && ' (ativo)'}
          {subscription.status === 'canceled' && ' (cancelado)'}
        </Alert>
      )}

      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={3}
        justifyContent="center"
        alignItems={{ xs: 'center', md: 'stretch' }}
      >
        {plans.map((plan) => {
          const isCurrent = currentPlanName === plan.name
          const isPopular = plan.name === 'pro'

          return (
            <Card
              key={plan.id}
              variant={isPopular ? 'elevation' : 'outlined'}
              sx={{
                width: { xs: '100%', md: 340 },
                position: 'relative',
                border: isPopular ? 2 : undefined,
                borderColor: isPopular ? 'primary.main' : undefined,
                display: 'flex',
                flexDirection: 'column',
              }}
              elevation={isPopular ? 8 : 1}
            >
              {isPopular && (
                <Chip
                  icon={<StarIcon />}
                  label="Mais popular"
                  color="primary"
                  size="small"
                  sx={{
                    position: 'absolute',
                    top: -12,
                    left: '50%',
                    transform: 'translateX(-50%)',
                  }}
                />
              )}

              <CardContent sx={{ flexGrow: 1, pt: isPopular ? 3 : 2 }}>
                <Typography variant="h5" fontWeight={700} gutterBottom>
                  {plan.displayName}
                </Typography>

                <Typography variant="h4" fontWeight={800} color="primary" gutterBottom>
                  {formatPrice(plan.priceCents)}
                  {plan.priceCents > 0 && (
                    <Typography component="span" variant="body2" color="text.secondary">
                      /mês
                    </Typography>
                  )}
                </Typography>

                <Stack spacing={0.5} mt={2}>
                  <FeatureRow
                    label="Alertas ativos"
                    value={formatLimit(plan.maxActiveAlerts)}
                  />
                  <FeatureRow
                    label="Frequência mínima"
                    value={formatFrequency(plan.minFrequencyMinutes)}
                  />
                  <FeatureRow
                    label="Histórico de preços"
                    value={formatLimit(plan.priceHistoryDays, ' dias')}
                  />
                  <FeatureRow
                    label="Fontes de pesquisa"
                    value={formatLimit(plan.maxSources)}
                  />
                  <FeatureRow
                    label="Notificações push"
                    value={plan.hasPushNotifications}
                  />
                  <FeatureRow
                    label="WhatsApp"
                    value={plan.hasWhatsappNotifications}
                  />
                  <FeatureRow
                    label="Acesso à API"
                    value={plan.hasApiAccess}
                  />
                </Stack>
              </CardContent>

              <CardActions sx={{ p: 2, pt: 0 }}>
                {isCurrent ? (
                  <Stack width="100%" spacing={1}>
                    <Button variant="outlined" disabled fullWidth>
                      Plano atual
                    </Button>
                    {plan.name !== 'free' && (
                      <Button
                        variant="text"
                        color="error"
                        size="small"
                        fullWidth
                        disabled={actionLoading === 'cancel'}
                        onClick={handleCancel}
                      >
                        {actionLoading === 'cancel' ? (
                          <CircularProgress size={20} />
                        ) : (
                          'Cancelar assinatura'
                        )}
                      </Button>
                    )}
                  </Stack>
                ) : (
                  <Button
                    variant={isPopular ? 'contained' : 'outlined'}
                    fullWidth
                    disabled={actionLoading !== null}
                    onClick={() => handleSubscribe(plan.id)}
                  >
                    {actionLoading === plan.id ? (
                      <CircularProgress size={20} />
                    ) : plan.priceCents === 0 ? (
                      'Usar grátis'
                    ) : (
                      'Assinar'
                    )}
                  </Button>
                )}
              </CardActions>
            </Card>
          )
        })}
      </Stack>
    </Box>
  )
}
