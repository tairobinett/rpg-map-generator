import { useState } from 'react'
import {
  Box,
  Button,
  Checkbox,
  Container,
  Divider,
  FormControlLabel,
  Grid,
  Paper,
  Slider,
  Stack,
  TextField,
  Typography,
  CircularProgress,
  Tooltip,
  IconButton,
  Collapse,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  alpha,
} from '@mui/material'
import { createTheme, ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh'
import DownloadIcon from '@mui/icons-material/Download'
import MapIcon from '@mui/icons-material/Map'
import WaterIcon from '@mui/icons-material/Water'
import HomeIcon from '@mui/icons-material/Home'
import RouteIcon from '@mui/icons-material/Route'
import GridOnIcon from '@mui/icons-material/GridOn'
import LandscapeIcon from '@mui/icons-material/Landscape'
import ParkIcon from '@mui/icons-material/Park'

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#c8a96e',
      light: '#e2c99a',
      dark: '#96784a',
    },
    secondary: {
      main: '#6b9e6b',
      light: '#8fc08f',
      dark: '#4a7a4a',
    },
    background: {
      default: '#1a1a14',
      paper: '#252520',
    },
    text: {
      primary: '#e8e0cc',
      secondary: '#a09880',
    },
    divider: 'rgba(200,169,110,0.15)',
  },
  typography: {
    fontFamily: '"Cinzel", "Palatino Linotype", serif',
    h4: {
      fontFamily: '"Cinzel Decorative", "Cinzel", serif',
      letterSpacing: '0.08em',
      fontWeight: 700,
    },
    h6: {
      fontFamily: '"Cinzel", serif',
      letterSpacing: '0.05em',
      fontWeight: 600,
    },
    body1: {
      fontFamily: '"Crimson Text", "Georgia", serif',
      fontSize: '1rem',
    },
    body2: {
      fontFamily: '"Crimson Text", "Georgia", serif',
      fontSize: '0.9rem',
    },
    caption: {
      fontFamily: '"Crimson Text", "Georgia", serif',
      fontSize: '0.8rem',
    },
  },
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderColor: 'rgba(200,169,110,0.2)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          fontFamily: '"Cinzel", serif',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiInputBase-root': {
            fontFamily: '"Crimson Text", Georgia, serif',
          },
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          color: '#c8a96e',
          '& .MuiSlider-thumb': {
            backgroundColor: '#c8a96e',
            '&:hover': {
              boxShadow: '0 0 0 8px rgba(200,169,110,0.16)',
            },
          },
          '& .MuiSlider-rail': {
            backgroundColor: 'rgba(200,169,110,0.2)',
          },
        },
      },
    },
    MuiFormControlLabel: {
      styleOverrides: {
        label: {
          fontFamily: '"Crimson Text", Georgia, serif',
          fontSize: '1rem',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontFamily: '"Cinzel", serif',
          fontSize: '0.7rem',
          letterSpacing: '0.05em',
        },
      },
    },
  },
})

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 2.5 }}>
      <Box sx={{ color: 'primary.main', display: 'flex', alignItems: 'center' }}>
        {icon}
      </Box>
      <Typography variant="h6" sx={{ fontSize: '0.85rem', color: 'primary.main' }}>
        {title}
      </Typography>
      <Box sx={{ flex: 1, height: '1px', background: 'linear-gradient(90deg, rgba(200,169,110,0.4) 0%, transparent 100%)' }} />
    </Stack>
  )
}

function CoverageSlider({
  label,
  coverage,
  onCoverageChange,
}: {
  label: string
  coverage: number
  onCoverageChange: (v: number) => void
}) {
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1.5, fontSize: '0.9rem' }}>
        {label}
      </Typography>
      <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block', mb: 0.5 }}>
        Coverage — {coverage}%
      </Typography>
      <Slider
        size="small"
        value={coverage}
        onChange={(_, v) => onCoverageChange(v as number)}
        valueLabelDisplay="auto"
      />
    </Box>
  )
}

function FeatureRow({
  label,
  icon,
  enabled,
  onToggle,
  children,
}: {
  label: string
  icon: React.ReactNode
  enabled: boolean
  onToggle: () => void
  children?: React.ReactNode
}) {
  return (
    <Box sx={{ mb: 2 }}>
      <FormControlLabel
        control={
          <Checkbox
            checked={enabled}
            onChange={onToggle}
            sx={{
              color: 'rgba(200,169,110,0.4)',
              '&.Mui-checked': { color: 'primary.main' },
            }}
          />
        }
        label={
          <Stack direction="row" alignItems="center" spacing={1}>
            <Box sx={{ color: enabled ? 'primary.main' : 'text.secondary', display: 'flex' }}>{icon}</Box>
            <span style={{ color: enabled ? undefined : 'rgba(160,152,128,0.5)' }}>{label}</span>
          </Stack>
        }
      />
      <Collapse in={enabled}>
        <Box sx={{ ml: 5, mt: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  )
}

export default function App() {
  const [imageURL, setImageURL] = useState('')
  const [loading, setLoading] = useState(false)
  const [seed, setSeed] = useState('')
  const [height, setHeight] = useState(15)
  const [width, setWidth] = useState(15)
  const [river_width, setRiverWidth] = useState(1)
  const [road_width, setRoadWidth] = useState(1)

  const [rawValues, setRawValues] = useState({
    height: '15',
    width: '15',
    river_width: '1',
    road_width: '1',
  })

  type RawKey = keyof typeof rawValues

  const setterMap: Record<RawKey, (n: number) => void> = {
    height: setHeight,
    width: setWidth,
    river_width: setRiverWidth,
    road_width: setRoadWidth,
  }

  const limitsMap: Record<RawKey, [number, number]> = {
    height:      [5, 60],
    width:       [5, 60],
    river_width: [1, 5],
    road_width:  [1, 5],
  }

  const handleChange = (key: RawKey) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value
    setRawValues(prev => ({ ...prev, [key]: raw }))
    // Commit immediately so spinner clicks (which skip onBlur) still update state
    const parsed = parseInt(raw, 10)
    if (!isNaN(parsed)) {
      const [min, max] = limitsMap[key]
      const clamped = Math.min(max, Math.max(min, parsed))
      setterMap[key](clamped)
    }
  }

  const handleBlur = (key: RawKey, min: number, max: number, setter: (n: number) => void) => () => {
    const parsed = parseInt(rawValues[key], 10)
    const clamped = isNaN(parsed) ? min : Math.min(max, Math.max(min, parsed))
    setter(clamped)
    setRawValues(prev => ({ ...prev, [key]: String(clamped) }))
  }
  const [flower_coverage, setFlowerCoverage] = useState(25)
  const [rock_coverage, setRockCoverage] = useState(25)
  const [bush_coverage, setBushCoverage] = useState(25)
  const [grid_toggle, setGridToggle] = useState(true)
  const [river_enabled, setRiverEnabled] = useState(true)
  const [building_enabled, setBuildingEnabled] = useState(true)
  const [road_enabled, setRoadEnabled] = useState(true)
  const [biome, setBiome] = useState<'grassland' | 'snow' | 'desert'>('grassland')

  const foliageLabels: Record<'grassland' | 'snow' | 'desert', [string, string, string]> = {
    grassland: ['Flowers', 'Rocks', 'Bushes'],
    snow:      ['Snowdrifts', 'Rocks', 'Bushes'],
    desert:    ['Bones', 'Rocks', 'Cacti'],
  }
  const [foliageLabel1, foliageLabel2, foliageLabel3] = foliageLabels[biome]

  const generateImage = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://34.138.246.196:8000/generate_map', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          seed,
          height,
          width,
          river_width,
          road_width,
          flower_coverage,
          rock_coverage,
          bush_coverage,
          grid: grid_toggle,
          river_enabled,
          building_enabled,
          road_enabled,
          biome,
        }),
      })
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      setImageURL(url)
    } catch (e) {
      console.error('Error: ', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          background: `
            #1a1a14
          `,
          py: 4,
        }}
      >
        <style>{`@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');`}</style>

        <Container maxWidth="xl">
          {/* header */}
          <Box sx={{ textAlign: 'center', mb: 5 }}>
            <Stack direction="row" justifyContent="center" alignItems="center" spacing={2} sx={{ mb: 1 }}>
              <Box sx={{ color: 'primary.main', opacity: 0.6 }}>✦</Box>
              <MapIcon sx={{ color: 'primary.main', fontSize: 32 }} />
              <Box sx={{ color: 'primary.main', opacity: 0.6 }}>✦</Box>
            </Stack>
            <Typography
              variant="h4"
              sx={{
                fontSize: { xs: '1.4rem', md: '1.9rem' },
                background: 'linear-gradient(135deg, #e2c99a 0%, #c8a96e 50%, #96784a 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 0.5,
              }}
            >
              PandaMaps - an RPG Map Generator
            </Typography>
          </Box>

          <Grid container spacing={3}>
            {/* left panel - controls */}
            <Grid size={{ xs: 12, lg: 4 }}>
              <Stack spacing={2.5}>

                {/* map settings */}
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    border: '1px solid',
                    borderColor: 'divider',
                    background: alpha('#252520', 0.8),
                  }}
                >
                  <SectionHeader icon={<MapIcon fontSize="small" />} title="Map Settings" />

                  <Stack spacing={2}>
                    <TextField
                      label="Seed"
                      placeholder="Enter any text..."
                      value={seed}
                      onChange={e => setSeed(e.target.value)}
                      size="small"
                      fullWidth
                      variant="outlined"
                      InputProps={{
                        endAdornment: (
                          <Tooltip title="Click for a random seed">
                            <IconButton size="small" onClick={() => setSeed(Math.random().toString(36).slice(2))}>
                              <AutoFixHighIcon fontSize="small" sx={{ color: 'primary.main', opacity: 0.7 }} />
                            </IconButton>
                          </Tooltip>
                        ),
                      }}
                    />
                    <Grid container spacing={2}>
                      <Grid size={6}>
                        <TextField
                          label="Width"
                          type="number"
                          value={rawValues.width}
                          onChange={handleChange('width')}
                          onBlur={handleBlur('width', 5, 60, setWidth)}
                          size="small"
                          fullWidth
                          slotProps={{ htmlInput: { min: 5, max: 60, step: 1 } }}
                        />
                      </Grid>
                      <Grid size={6}>
                        <TextField
                          label="Height"
                          type="number"
                          value={rawValues.height}
                          onChange={handleChange('height')}
                          onBlur={handleBlur('height', 5, 60, setHeight)}
                          size="small"
                          fullWidth
                          slotProps={{ htmlInput: { min: 5, max: 60, step: 1 } }}
                        />
                      </Grid>
                    </Grid>

                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={grid_toggle}
                          onChange={() => setGridToggle(!grid_toggle)}
                          icon={<GridOnIcon sx={{ color: 'rgba(200,169,110,0.3)' }} />}
                          checkedIcon={<GridOnIcon sx={{ color: 'primary.main' }} />}
                        />
                      }
                      label="Show Grid Overlay"
                    />

                    <FormControl size="small" fullWidth>
                      <InputLabel sx={{ fontFamily: '"Crimson Text", Georgia, serif' }}>Biome</InputLabel>
                      <Select
                        value={biome}
                        label="Biome"
                        onChange={e => setBiome(e.target.value as 'grassland' | 'snow' | 'desert')}
                        sx={{ fontFamily: '"Crimson Text", Georgia, serif' }}
                      >
                        <MenuItem value="grassland">Grassland</MenuItem>
                        <MenuItem value="snow">Tundra</MenuItem>
                        <MenuItem value="desert">Desert</MenuItem>
                      </Select>
                    </FormControl>
                  </Stack>
                </Paper>

                {/* optional map features */}
                <Paper
                  variant="outlined"
                  sx={{ p: 3, border: '1px solid', borderColor: 'divider', background: alpha('#252520', 0.8) }}
                >
                  <SectionHeader icon={<LandscapeIcon fontSize="small" />} title="Features" />

                  <FeatureRow
                    label="River"
                    icon={<WaterIcon fontSize="small" />}
                    enabled={river_enabled}
                    onToggle={() => setRiverEnabled(!river_enabled)}
                  >
                    <TextField
                      label="River Width"
                      type="number"
                      value={rawValues.river_width}
                      onChange={handleChange('river_width')}
                      onBlur={handleBlur('river_width', 1, 5, setRiverWidth)}
                      size="small"
                      slotProps={{ htmlInput: { min: 1, max: 5, step: 1 } }}
                      sx={{ width: '100%', maxWidth: 160 }}
                    />
                  </FeatureRow>

                  <FeatureRow
                    label="Building"
                    icon={<HomeIcon fontSize="small" />}
                    enabled={building_enabled}
                    onToggle={() => setBuildingEnabled(!building_enabled)}
                  />

                  <FeatureRow
                    label="Road"
                    icon={<RouteIcon fontSize="small" />}
                    enabled={road_enabled}
                    onToggle={() => setRoadEnabled(!road_enabled)}
                  >
                    <TextField
                      label="Road Width"
                      type="number"
                      value={rawValues.road_width}
                      onChange={handleChange('road_width')}
                      onBlur={handleBlur('road_width', 1, 5, setRoadWidth)}
                      size="small"
                      slotProps={{ htmlInput: { min: 1, max: 5, step: 1 } }}
                      sx={{ width: '100%', maxWidth: 160 }}
                    />
                  </FeatureRow>
                </Paper>

                {/* foliage and objects */}
                <Paper
                  variant="outlined"
                  sx={{ p: 3, border: '1px solid', borderColor: 'divider', background: alpha('#252520', 0.8) }}
                >
                  <SectionHeader icon={<ParkIcon fontSize="small" />} title="Foliage & Objects" />

                  <CoverageSlider
                    label={foliageLabel1}
                    coverage={flower_coverage}
                    onCoverageChange={setFlowerCoverage}
                  />
                  <Divider sx={{ my: 2, borderColor: 'divider' }} />
                  <CoverageSlider
                    label={foliageLabel2}
                    coverage={rock_coverage}
                    onCoverageChange={setRockCoverage}
                  />
                  <Divider sx={{ my: 2, borderColor: 'divider' }} />
                  <CoverageSlider
                    label={foliageLabel3}
                    coverage={bush_coverage}
                    onCoverageChange={setBushCoverage}
                  />
                </Paper>

                {/* generate button */}
                <Button
                  variant="contained"
                  size="large"
                  onClick={generateImage}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <AutoFixHighIcon />}
                  fullWidth
                  sx={{
                    py: 1.8,
                    fontSize: '0.9rem',
                    background: 'linear-gradient(135deg, #96784a 0%, #c8a96e 50%, #96784a 100%)',
                    backgroundSize: '200% 100%',
                    color: '#1a1a14',
                    fontWeight: 700,
                    border: '1px solid rgba(200,169,110,0.5)',
                    boxShadow: '0 4px 20px rgba(200,169,110,0.2)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      backgroundPosition: '100% 0',
                      boxShadow: '0 6px 28px rgba(200,169,110,0.35)',
                      transform: 'translateY(-1px)',
                    },
                    '&:disabled': {
                      background: 'rgba(200,169,110,0.2)',
                      color: 'rgba(200,169,110,0.4)',
                    },
                  }}
                >
                  {loading ? 'Generating Map...' : 'Generate Map'}
                </Button>

              </Stack>
            </Grid>

            {/* right panel - map output */}
            <Grid size={{ xs: 12, lg: 8 }}>
              <Paper
                variant="outlined"
                sx={{
                  border: '1px solid',
                  borderColor: 'divider',
                  background: alpha('#252520', 0.6),
                  minHeight: 500,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  overflow: 'hidden',
                  position: 'relative',
                }}
              >
                {!imageURL && !loading && (
                  <Box sx={{ textAlign: 'center', p: 6, opacity: 0.4 }}>
                    <MapIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                    <Typography variant="caption" sx={{ color: 'text.secondary' }}>
                      Configure settings and click Generate
                    </Typography>
                  </Box>
                )}

                {loading && (
                  <Box sx={{ textAlign: 'center', p: 6 }}>
                    <CircularProgress sx={{ color: 'primary.main', mb: 3 }} size={48} thickness={2} />
                    <Typography variant="body1" sx={{ color: 'text.secondary', fontStyle: 'italic' }}>
                      Shaping the world…
                    </Typography>
                  </Box>
                )}

                {imageURL && !loading && (
                  <Box sx={{ width: '100%', position: 'relative' }}>
                    {/* toolbar */}
                    <Box
                      sx={{
                        px: 2,
                        py: 1.5,
                        borderBottom: '1px solid',
                        borderColor: 'divider',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                      }}
                    >
                      <Button
                        component="a"
                        href={imageURL}
                        download={`map_${seed || 'random'}.png`}
                        size="small"
                        startIcon={<DownloadIcon fontSize="small" />}
                        sx={{
                          color: 'primary.main',
                          borderColor: 'primary.dark',
                          fontFamily: '"Cinzel", serif',
                          fontSize: '0.7rem',
                          letterSpacing: '0.08em',
                        }}
                        variant="outlined"
                      >
                        Download
                      </Button>
                    </Box>

                    <Box sx={{ p: 2 }}>
                      <img
                        src={imageURL}
                        alt="Generated terrain map"
                        style={{
                          width: '100%',
                          height: 'auto',
                          display: 'block',
                          borderRadius: 2,
                        }}
                      />
                    </Box>
                  </Box>
                )}
              </Paper>

              {/* attribution */}
              <Typography
                variant="caption"
                sx={{ display: 'block', textAlign: 'center', mt: 1.5, color: 'text.secondary', fontStyle: 'italic' }}
              >
                Assets by{' '}
                <Box component="a" href="https://2minutetabletop.com" sx={{ color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                  2 Minute Tabletop
                </Box>
                , licensed under{' '}
                <Box component="a" href="https://creativecommons.org/licenses/by-nc/4.0/" sx={{ color: 'primary.main', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}>
                  CC BY-NC 4.0
                </Box>
                . Some assets have been modified from their original form.
              </Typography>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  )
}
