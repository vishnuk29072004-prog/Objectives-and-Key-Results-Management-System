import { forwardRef } from 'react'
import MuiStack from '@mui/material/Stack'

/** Style props removed from MUI v9 Stack — map them into `sx` so they don't hit the DOM. */
const STYLE_PROPS = [
  'alignItems',
  'justifyContent',
  'flexWrap',
  'alignContent',
  'alignSelf',
  'justifyItems',
  'justifySelf',
  'm',
  'mt',
  'mr',
  'mb',
  'ml',
  'mx',
  'my',
  'p',
  'pt',
  'pr',
  'pb',
  'pl',
  'px',
  'py',
  'width',
  'height',
  'minWidth',
  'maxWidth',
  'minHeight',
  'maxHeight',
  'display',
  'overflow',
  'gap',
  'rowGap',
  'columnGap',
  'flex',
  'flexGrow',
  'flexShrink',
  'flexBasis',
  'bgcolor',
  'color',
  'borderRadius',
  'position',
  'top',
  'right',
  'bottom',
  'left',
]

export const Stack = forwardRef(function Stack(props, ref) {
  const rest = { ...props }
  const sxExtra = {}

  for (const key of STYLE_PROPS) {
    if (rest[key] !== undefined) {
      sxExtra[key] = rest[key]
      delete rest[key]
    }
  }

  const { sx, ...other } = rest
  other.sx = sx ? (Array.isArray(sx) ? [sxExtra, ...sx] : [sxExtra, sx]) : sxExtra

  return <MuiStack ref={ref} {...other} />
})

export default Stack
