import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from './ErrorBoundary'

function Boom() {
  throw new Error('boom')
}

describe('ErrorBoundary', () => {
  it('renders children when nothing throws', () => {
    render(
      <ErrorBoundary fallback={<p>fallback</p>}>
        <p>all good</p>
      </ErrorBoundary>,
    )

    expect(screen.getByText('all good')).toBeInTheDocument()
  })

  it('renders the fallback instead of crashing when a child throws', () => {
    // React logs the caught error to the console; silence it for this expected-error test.
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    render(
      <ErrorBoundary fallback={<p>fallback shown</p>}>
        <Boom />
      </ErrorBoundary>,
    )

    expect(screen.getByText('fallback shown')).toBeInTheDocument()
    expect(screen.queryByText('all good')).not.toBeInTheDocument()

    consoleError.mockRestore()
  })
})
