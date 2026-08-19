import { Suspense, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Html } from '@react-three/drei'
import { hasWebGL } from '../hasWebGL'

// Approximate marker positions on the stylized figure below. This is a simplified,
// non-mirrored convention (screen-left = left_arm/left_leg) for a stylized aid, not an
// anatomically precise diagram — good enough to show roughly where a condition sits.
const REGION_POSITIONS = {
  head: [0, 1.68, 0.14],
  chest: [0, 1.32, 0.24],
  abdomen: [0, 1.02, 0.22],
  back: [0, 1.2, -0.24],
  pelvis: [0, 0.78, 0.18],
  left_arm: [-0.38, 1.05, 0],
  right_arm: [0.38, 1.05, 0],
  left_leg: [-0.12, 0.35, 0.08],
  right_leg: [0.12, 0.35, 0.08],
  general: [0, 2.0, 0],
}

const SKIN = '#E8C9A0'
const CLOTHES = '#0E7A5F'
const LEGS = '#2A2A2A'

function BodyMesh() {
  return (
    <group>
      <mesh position={[0, 1.65, 0]}>
        <sphereGeometry args={[0.15, 24, 24]} />
        <meshStandardMaterial color={SKIN} />
      </mesh>
      <mesh position={[0, 1.2, 0]}>
        <cylinderGeometry args={[0.22, 0.26, 0.6, 16]} />
        <meshStandardMaterial color={CLOTHES} />
      </mesh>
      <mesh position={[0, 0.78, 0]}>
        <cylinderGeometry args={[0.2, 0.18, 0.25, 16]} />
        <meshStandardMaterial color={CLOTHES} />
      </mesh>
      <mesh position={[-0.35, 1.05, 0]} rotation={[0, 0, 0.15]}>
        <cylinderGeometry args={[0.06, 0.06, 0.6, 12]} />
        <meshStandardMaterial color={SKIN} />
      </mesh>
      <mesh position={[0.35, 1.05, 0]} rotation={[0, 0, -0.15]}>
        <cylinderGeometry args={[0.06, 0.06, 0.6, 12]} />
        <meshStandardMaterial color={SKIN} />
      </mesh>
      <mesh position={[-0.12, 0.32, 0]}>
        <cylinderGeometry args={[0.08, 0.08, 0.7, 12]} />
        <meshStandardMaterial color={LEGS} />
      </mesh>
      <mesh position={[0.12, 0.32, 0]}>
        <cylinderGeometry args={[0.08, 0.08, 0.7, 12]} />
        <meshStandardMaterial color={LEGS} />
      </mesh>
    </group>
  )
}

function ConditionMarker({ condition, isSelected, onSelect }) {
  const position = REGION_POSITIONS[condition.body_region] || REGION_POSITIONS.general
  return (
    <mesh
      position={position}
      onClick={(event) => {
        event.stopPropagation()
        onSelect(condition)
      }}
    >
      <sphereGeometry args={[0.055, 16, 16]} />
      <meshStandardMaterial
        color={isSelected ? '#C4331B' : '#F2A900'}
        emissive={isSelected ? '#C4331B' : '#000000'}
        emissiveIntensity={0.35}
      />
      {isSelected && (
        <Html distanceFactor={8}>
          <div className="body3d-tooltip">
            <strong>{condition.name}</strong>
            {condition.diagnosed_date && <div>Diagnosed {condition.diagnosed_date}</div>}
            {condition.notes && <div>{condition.notes}</div>}
          </div>
        </Html>
      )}
    </mesh>
  )
}

// Conditions with no body_region at all (vs. an explicit "general") aren't shown here —
// they're systemic/unspecified and belong in the plain-text conditions list instead.
export function Body3D({ conditions }) {
  const [selectedId, setSelectedId] = useState(null)
  const localized = conditions.filter((c) => c.body_region)

  if (localized.length === 0) {
    return <p className="body3d-empty">No localized conditions to show on the body view.</p>
  }

  if (!hasWebGL()) {
    return (
      <p className="body3d-empty">
        The 3D view isn't supported on this device or browser — see the conditions list below.
      </p>
    )
  }

  return (
    <div className="body3d-canvas">
      <Canvas camera={{ position: [0, 1.2, 2.4], fov: 45 }} dpr={[1, 2]} frameloop="demand">
        <ambientLight intensity={0.7} />
        <directionalLight position={[2, 3, 2]} intensity={0.8} />
        <Suspense fallback={null}>
          <BodyMesh />
          {localized.map((c) => (
            <ConditionMarker
              key={c.id}
              condition={c}
              isSelected={selectedId === c.id}
              onSelect={(cond) => setSelectedId((current) => (current === cond.id ? null : cond.id))}
            />
          ))}
        </Suspense>
        <OrbitControls enablePan={false} minDistance={1.5} maxDistance={4} />
      </Canvas>
    </div>
  )
}
