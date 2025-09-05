export function confirmViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 300))
}

export function skipViolation(violationId: string) {
  return new Promise<void>((resolve) => setTimeout(resolve, 200))
}

