export interface Point { x: number; y: number }
export interface CameraRegion {
  stopLine?: [Point, Point]
  lineB?: [Point, Point]
}
