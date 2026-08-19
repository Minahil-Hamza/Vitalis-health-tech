import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Body3D } from './Body3D'
import { hasWebGL } from '../hasWebGL'

// jsdom has no real WebGL context, so react-three-fiber's <Canvas> can't actually render
// in tests, and jsdom's own canvas.getContext('webgl') returns null by default anyway —
// hasWebGL() is mocked explicitly per test so each path is exercised deliberately rather
// than relying on jsdom's incidental behavior.
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }) => <div data-testid="mock-canvas">{children}</div>,
}))
vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  Html: ({ children }) => <div>{children}</div>,
}))
vi.mock('../hasWebGL', () => ({ hasWebGL: vi.fn() }))

describe('Body3D', () => {
  beforeEach(() => {
    hasWebGL.mockReturnValue(true)
  })

  it('shows an empty-state message when no conditions have a body_region', () => {
    render(<Body3D conditions={[{ id: '1', name: 'Diabetes', body_region: null }]} />)

    expect(screen.getByText(/no localized conditions/i)).toBeInTheDocument()
    expect(screen.queryByTestId('mock-canvas')).not.toBeInTheDocument()
  })

  it('renders the canvas when at least one condition has a body_region and WebGL is available', () => {
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

  it('falls back to a message instead of the canvas when WebGL is unavailable', () => {
    hasWebGL.mockReturnValue(false)

    render(<Body3D conditions={[{ id: '2', name: 'Asthma', body_region: 'chest' }]} />)

    expect(screen.getByText(/isn't supported on this device/i)).toBeInTheDocument()
    expect(screen.queryByTestId('mock-canvas')).not.toBeInTheDocument()
  })
})
