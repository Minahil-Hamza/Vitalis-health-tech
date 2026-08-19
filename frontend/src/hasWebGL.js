// Best-effort WebGL support check, so Body3D can degrade to a plain message instead of
// attempting a Three.js render (and a blank canvas / console errors) on a device or
// browser without WebGL — a real possibility on some low-end phones.
export function hasWebGL() {
  try {
    const canvas = document.createElement('canvas')
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    )
  } catch {
    return false
  }
}
