/**
 * Bivariate Choropleth Color Scheme
 * 3x3 grid classification for Conflict Proneness (CP) vs Climate Risk (CR)
 */

export interface BivariateClass {
  cp_class: 1 | 2 | 3
  cr_class: 1 | 2 | 3
  color: string
  label: string
}

// 9-class bivariate color scheme (sequential, diverging)
export const BIVARIATE_COLORS: Record<string, BivariateClass> = {
  '3-3': { cp_class: 3, cr_class: 3, color: '#d73027', label: 'High CP, High CR' },      // Dark Red
  '3-2': { cp_class: 3, cr_class: 2, color: '#fc8d59', label: 'High CP, Med CR' },       // Orange
  '3-1': { cp_class: 3, cr_class: 1, color: '#fee08b', label: 'High CP, Low CR' },       // Yellow
  '2-3': { cp_class: 2, cr_class: 3, color: '#e0f3f8', label: 'Med CP, High CR' },       // Light Blue
  '2-2': { cp_class: 2, cr_class: 2, color: '#abd9e9', label: 'Med CP, Med CR' },        // Medium Blue
  '2-1': { cp_class: 2, cr_class: 1, color: '#74add1', label: 'Med CP, Low CR' },        // Dark Blue
  '1-3': { cp_class: 1, cr_class: 3, color: '#4575b4', label: 'Low CP, High CR' },       // Darker Blue
  '1-2': { cp_class: 1, cr_class: 2, color: '#313695', label: 'Low CP, Med CR' },        // Navy
  '1-1': { cp_class: 1, cr_class: 1, color: '#f7f7f7', label: 'Low CP, Low CR' },        // Light Gray
}

export function getBivariateClass(cpScore: number, crScore: number): string {
  const cpClass = cpScore >= 6.67 ? 3 : cpScore >= 3.34 ? 2 : 1
  const crClass = crScore >= 6.67 ? 3 : crScore >= 3.34 ? 2 : 1
  return `${cpClass}-${crClass}`
}

export function getBivariateColor(cpScore: number, crScore: number): string {
  const classKey = getBivariateClass(cpScore, crScore)
  return BIVARIATE_COLORS[classKey]?.color || '#cccccc'
}

export function getIndicatorColor(score: number): string {
  if (score >= 7.5) return '#d73027'
  if (score >= 5.0) return '#fc8d59'
  if (score >= 2.5) return '#fee08b'
  return '#91cf60'
}

export function getRiskCategory(score: number): string {
  if (score >= 7.5) return 'Very High'
  if (score >= 5.0) return 'High'
  if (score >= 2.5) return 'Medium'
  return 'Low'
}
