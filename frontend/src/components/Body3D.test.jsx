import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Body3D } from './Body3D'

// jsdom has no WebGL context, so react-three-fiber's <Canvas> can't actually render in
// tests. The empty-state path (no localized conditions) never reaches <Canvas> at all,
// so it's tested directly; the populated path mocks the 3D libraries to confirm the
// component picks the right conditions and doesn't crash, without exercising real WebGL.
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }) => <div data-testid="mock-canvas">{children}</div>,
}))
vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  Html: ({ children }) => <div>{children}</div>,
}))

describe('Body3D', () => {
  it('shows an empty-state message when no conditions have a body_region', () => {
    render(<Body3D conditions={[{ id: '1', name: 'Diabetes', body_region: null }]} />)

    expect(screen.getByText(/no localized conditions/i)).toBeInTheDocument()
    expect(screen.queryByTestId('mock-canvas')).not.toBeInTheDocument()
  })

  it('renders the canvas when at least one condition has a body_region', () => {
    render(
      <Body3D
        conditions={[
          { id: '1', name: 'Diabetes', body_region: null },
          { id: '2', name: 'Asthma', body_region: 'chest', diagnosed_date: '2018-05-01', notes: null },
        ]}
      />,
    )

    expect(screen.getByTestId('mock-canvas')).toBeInTheDocument()
    expect(screen.queryByText(/no localized conditions/i)).not.toBeInTheDocument()
  })
})
