/**
 * Tests for components/common/ConfirmationDialog.tsx
 */

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ConfirmationDialog } from '@/components/common/ConfirmationDialog'

const defaultProps = {
  open: true,
  title: 'Delete item',
  message: 'Are you sure you want to delete this item?',
  onConfirm: vi.fn(),
  onCancel: vi.fn(),
}

describe('ConfirmationDialog', () => {
  it('renders title and message when open', () => {
    render(<ConfirmationDialog {...defaultProps} />)

    expect(screen.getByText('Delete item')).toBeInTheDocument()
    expect(
      screen.getByText('Are you sure you want to delete this item?'),
    ).toBeInTheDocument()
  })

  it('shows default button labels', () => {
    render(<ConfirmationDialog {...defaultProps} />)

    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('shows custom button labels when provided', () => {
    render(
      <ConfirmationDialog
        {...defaultProps}
        confirmLabel="Yes, delete"
        cancelLabel="Go back"
      />,
    )

    expect(screen.getByRole('button', { name: 'Yes, delete' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Go back' })).toBeInTheDocument()
  })

  it('calls onConfirm when the confirm button is clicked', async () => {
    const onConfirm = vi.fn()
    render(<ConfirmationDialog {...defaultProps} onConfirm={onConfirm} />)

    await userEvent.click(screen.getByRole('button', { name: 'Confirm' }))

    expect(onConfirm).toHaveBeenCalledOnce()
  })

  it('calls onCancel when the cancel button is clicked', async () => {
    const onCancel = vi.fn()
    render(<ConfirmationDialog {...defaultProps} onCancel={onCancel} />)

    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('does not render when open is false', () => {
    render(<ConfirmationDialog {...defaultProps} open={false} />)

    expect(screen.queryByText('Delete item')).not.toBeInTheDocument()
  })
})
