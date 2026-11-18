// One dark palette per theme. Each feeds makeColors; surfaces sit under the scene's glass.
const palette = (
  label: string,
  id: string,
  roles: { accent: string; danger: string; success: string; warning: string; pro: string },
  surfaces: readonly [string, string, string, string],
  text: readonly [string, string, string],
  git: { added: string; removed: string; modified: string; merged: string },
) =>
  ({
    label,
    id,
    only: 'dark',
    roles,
    dark: {
      gray: {
        anchors: {
          'surface-0': surfaces[0],
          'surface-1': surfaces[1],
          'surface-2': surfaces[2],
          'surface-3': surfaces[3],
          'text-primary': text[0],
          'text-secondary': text[1],
          'text-muted': text[2],
        },
      },
      git,
    },
  }) as const

// VNU navy surfaces, the UIT logo blue as accent.
export const NAVY = palette(
  'UIT Navy',
  'uit-navy',
  { accent: '#3f78e0', danger: '#ee583a', success: '#26a146', warning: '#f6c445', pro: '#8a72e8' },
  ['#04102a', '#081734', '#0c1d3e', '#112447'],
  ['#eaf0fb', '#c3cfe6', '#94a6c8'],
  { added: '#52cf74', removed: '#f07a5f', modified: '#f6c445', merged: '#b3a3f7' },
)

// Rain-dark teal, with the wet glass of Building A.
export const MONSOON = palette(
  'UIT Monsoon',
  'uit-monsoon',
  { accent: '#2fb5a8', danger: '#f47c6a', success: '#4fcc7a', warning: '#f2c46a', pro: '#a898f4' },
  ['#061216', '#0a191e', '#0e2127', '#122930'],
  ['#e3f1f2', '#bcd3d6', '#8aa6ab'],
  { added: '#5ad08a', removed: '#f07a6a', modified: '#f2c46a', merged: '#b0a2f5' },
)

// Dusk violet over Metro Line 1, the sunset as accent.
export const METRO = palette(
  'UIT Metro Dusk',
  'uit-metro',
  { accent: '#e8743a', danger: '#ef4f6a', success: '#4cc38a', warning: '#f6c445', pro: '#b18cf2' },
  ['#120c22', '#181030', '#1f153a', '#271b45'],
  ['#f3ecfb', '#d2c6e6', '#a596c2'],
  { added: '#5fd39a', removed: '#f2708a', modified: '#f6c445', merged: '#c4a6f6' },
)

// Solder-mask green with copper and gold.
export const SILICON = palette(
  'UIT Silicon',
  'uit-silicon',
  { accent: '#30c4b0', danger: '#ef5d4a', success: '#52c96a', warning: '#e8b84a', pro: '#9b86f2' },
  ['#03120e', '#061a14', '#0a221a', '#0f2b21'],
  ['#e2f5ec', '#b9d8ca', '#86a999'],
  { added: '#62d47a', removed: '#f07a68', modified: '#e8b84a', merged: '#b2a2f4' },
)

// Lunar New Year wine red with hoa mai gold.
export const TET = palette(
  'UIT Tet Bloom',
  'uit-tet',
  { accent: '#e85a3a', danger: '#f04a6a', success: '#4cc36a', warning: '#f2b630', pro: '#c08af0' },
  ['#14070c', '#1c0a12', '#250e18', '#2e121f'],
  ['#fbeee8', '#e3cfc8', '#b99d97'],
  { added: '#62d07e', removed: '#f4708a', modified: '#f2b630', merged: '#d0a6f4' },
)
