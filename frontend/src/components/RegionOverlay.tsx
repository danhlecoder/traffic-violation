import type { CameraRegion, Point } from '../types/regions'

export default function RegionOverlay({
  region,
  toPixel,
  readOnly = false,
  tempLine,
  tempRoi,
}: {
  region?: CameraRegion
  toPixel: (pt: Point) => { x: number; y: number }
  readOnly?: boolean
  tempLine?: { p1?: Point; p2?: Point }
  tempRoi?: Point[]
}) {
  const hasRegion = Boolean(region?.stopLine)
  const hasTemp = Boolean(tempLine?.p1)
  if (!hasRegion && !hasTemp) return null

  return (
    <div className="region-overlay" style={readOnly ? { pointerEvents: 'none' } : undefined}>
      {region?.stopLine && (
        <svg className="region-svg">
          {(() => {
            const [a, b] = region.stopLine!
            const A = toPixel(a)
            const B = toPixel(b)
            return (
              <g>
                <line x1={A.x} y1={A.y} x2={B.x} y2={B.y} className="region-line" style={{ strokeWidth: 2 }} />
                <circle cx={A.x} cy={A.y} r={4} className="region-point" />
                <circle cx={B.x} cy={B.y} r={4} className="region-point" />
              </g>
            )
          })()}
        </svg>
      )}

      {region?.lineB && (
        <svg className="region-svg">
          {(() => {
            const [a, b] = region.lineB!
            const A = toPixel(a)
            const B = toPixel(b)
            return (
              <g>
                <line x1={A.x} y1={A.y} x2={B.x} y2={B.y} className="region-line" style={{ strokeWidth: 2, stroke: '#ffeb3b' }} />
                <circle cx={A.x} cy={A.y} r={4} className="region-point" />
                <circle cx={B.x} cy={B.y} r={4} className="region-point" />
              </g>
            )
          })()}
        </svg>
      )}

      {tempLine?.p1 && (
        <svg className="region-svg">
          {(() => {
            const A = toPixel(tempLine.p1!)
            const B = tempLine.p2 ? toPixel(tempLine.p2) : undefined
            return (
              <g>
                {B ? <line x1={A.x} y1={A.y} x2={B.x} y2={B.y} className="region-line temp" /> : null}
                <circle cx={A.x} cy={A.y} r={5} className="region-point temp" />
                {B ? <circle cx={B.x} cy={B.y} r={5} className="region-point temp" /> : null}
              </g>
            )
          })()}
        </svg>
      )}
    </div>
  )
}


