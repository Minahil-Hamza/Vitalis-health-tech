import { Component } from 'react'

// React error boundaries must be class components — there's no hook equivalent yet.
// Used around Body3D so a WebGL/Three.js runtime failure on some device degrades to
// the fallback UI instead of blanking the whole patient page.
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}
