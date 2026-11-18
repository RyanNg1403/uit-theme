import type { EngineInterface as Engine, Register, ThemeColor, ThemeSetArgs } from 'claude-code'

import { makeColors } from './make-colors.js'
import { DAWN, EXAM, METRO, MONSOON, NAVY, SILICON, TET, TRUNGTHU } from './palettes'
import { previewPage } from './preview'
import { SCENE as DAWN_SCENE } from './scenes/dawn'
import { SCENE as EXAM_SCENE } from './scenes/exam'
import { SCENE as METRO_SCENE } from './scenes/metro'
import { SCENE as MONSOON_SCENE } from './scenes/monsoon'
import { SCENE as NAVY_SCENE } from './scenes/navy'
import { SCENE as SILICON_SCENE } from './scenes/silicon'
import { SCENE as TET_SCENE } from './scenes/tet'
import { SCENE as TRUNGTHU_SCENE } from './scenes/trungthu'

type Palette = Parameters<typeof makeColors>[0]

interface Theme {
  id: string
  title: string
  blurb: string
  palette: Palette
  scheme?: 'light' | 'dark'
  /** Glass over an animated scene; absent for a still or plain look. */
  scene?: { svg: string; alt: string; tint: string; opacity: number }
  still?: string
  gradient?: readonly [ThemeColor, ThemeColor]
}

const THEMES: readonly Theme[] = [
  {
    id: 'navy',
    title: 'UIT Navy',
    blurb: 'Pixel campus by the lake at night, UIT constellation, crescent moon',
    palette: NAVY,
    scene: {
      svg: NAVY_SCENE,
      alt: 'A pixel-art university campus at night by a lake, with a UIT constellation and a crescent moon under a starry sky',
      tint: '#04102a',
      opacity: 0.72,
    },
  },
  {
    id: 'monsoon',
    title: 'Monsoon',
    blurb: 'Saigon rainy season: Building A in the rain, lightning, a wet plaza, the campus bus',
    palette: MONSOON,
    scene: {
      svg: MONSOON_SCENE,
      alt: 'A pixel-art campus building on a rainy night, with lightning, street lamps reflected on a wet plaza and people under umbrellas',
      tint: '#061216',
      opacity: 0.74,
    },
  },
  {
    id: 'metro',
    title: 'Metro Dusk',
    blurb: 'Metro Line 1 gliding past at sunset, Hanoi Highway traffic below',
    palette: METRO,
    scene: {
      svg: METRO_SCENE,
      alt: 'A pixel-art sunset with a white and blue metro train crossing an elevated viaduct, a campus tower and highway light trails',
      tint: '#120c22',
      opacity: 0.72,
    },
  },
  {
    id: 'silicon',
    title: 'Silicon',
    blurb: 'The campus as a circuit board: UIT processor, memory, data bus packets',
    palette: SILICON,
    scene: {
      svg: SILICON_SCENE,
      alt: 'A pixel-art circuit board seen from above, with a UIT processor, memory slots, blinking LEDs and packets running along copper traces',
      tint: '#03120e',
      opacity: 0.74,
    },
  },
  {
    id: 'tet',
    title: 'Tet Bloom',
    blurb: 'Lunar New Year on campus: hoa mai, red lanterns, fireworks',
    palette: TET,
    scene: {
      svg: TET_SCENE,
      alt: 'A pixel-art Lunar New Year night on campus, with a blooming yellow apricot tree, red lanterns, a greeting banner and fireworks',
      tint: '#14070c',
      opacity: 0.74,
    },
  },
  {
    id: 'trungthu',
    title: 'Trung Thu',
    blurb: 'Mid-Autumn on campus: full moon, star lanterns, a lion dance, mooncakes',
    palette: TRUNGTHU,
    scene: {
      svg: TRUNGTHU_SCENE,
      alt: 'A pixel-art Mid-Autumn night on campus, with a full moon, star lanterns, children in a lantern parade, a lion dance and mooncakes',
      tint: '#0b0a20',
      opacity: 0.72,
    },
  },
  {
    id: 'exam',
    title: 'Exam Night',
    blurb: 'The library at 2 AM in exam season: desk lamps, rain on the window, a phin of coffee',
    palette: EXAM,
    scene: {
      svg: EXAM_SCENE,
      alt: 'A pixel-art library late at night, with bookshelves, green desk lamps, a wall clock, rain on a tall window and a Vietnamese iced coffee dripping',
      tint: '#100b07',
      opacity: 0.74,
    },
  },
  {
    id: 'dawn',
    title: 'Campus Dawn',
    blurb: 'Sunrise over the lake by the dorms, mist, birds, bikes on the lakeside road (light)',
    palette: DAWN,
    scheme: 'light',
    scene: {
      svg: DAWN_SCENE,
      alt: 'A pixel-art sunrise over a lake, with dormitory blocks, a campus tower, mist on the water, birds and cyclists on a road',
      tint: '#f4efe6',
      opacity: 0.7,
    },
  },
  {
    id: 'still',
    title: 'Navy Still',
    blurb: 'The navy campus as a still picture',
    palette: NAVY,
    still: 'assets/campus-night.png',
  },
  {
    id: 'plain',
    title: 'Navy Plain',
    blurb: 'Navy colors on a plain gradient',
    palette: NAVY,
    gradient: ['#061636', '#04102a'],
  },
]

const ALIASES: Record<string, string> = { scene: 'navy', 'tet-bloom': 'tet', 'metro-dusk': 'metro', 'trung-thu': 'trungthu', 'mid-autumn': 'trungthu', 'exam-night': 'exam', 'campus-dawn': 'dawn' }
const STORE_KEY = 'theme'
const LEGACY_KEY = 'variant'
const PLUGIN = 'uit-theme'
const sceneName = (theme: Theme) => `uit-${theme.id}`

const COLORS = new Map(THEMES.map(theme => [theme.id, makeColors(theme.palette)]))

const findTheme = (word: string) => THEMES.find(theme => theme.id === (ALIASES[word] ?? word))

const lookFor = (theme: Theme): ThemeSetArgs => {
  const base = { colors: COLORS.get(theme.id)!.theme, overrideColorScheme: theme.scheme ?? 'dark' } as const

  if (theme.scene) {
    return {
      ...base,
      backdrop: { scene: sceneName(theme), glass: { blur: 14, tint: theme.scene.tint, opacity: theme.scene.opacity } },
    }
  }
  if (theme.still) {
    return { ...base, backdrop: { image: { source: theme.still } } }
  }

  return { ...base, backdrop: { gradient: { stops: [...theme.gradient!], angle: 180 } } }
}

const listing = (current: string) =>
  THEMES.map(theme => `${theme.id === current ? '>' : ' '} ${theme.id.padEnd(9)} ${theme.title}: ${theme.blurb}`).join('\n')

const USAGE = [
  '/uit <theme>       switch theme (navy, monsoon, metro, silicon, tet, trungthu, exam, dawn, still, plain)',
  '/uit next          cycle to the next theme',
  '/uit list          list themes',
  '/uit off           back to the default look',
  '/uit-preview       open a localhost gallery of every scene',
  '/uit-preview stop  stop the gallery server',
].join('\n')

// ---------------------------------------------------------------- preview server
// A python http.server on 127.0.0.1 serving a temp folder of the scenes. It lives as long
// as its stream loop: stopping it, or the module unloading, ends the child.
let server: { url: string; dir: string; stop: () => void } | undefined

async function startPreview($: Engine, current: string): Promise<string> {
  if (server) {
    return server.url
  }

  const made = await $.process.run(['python3', '-c', 'import tempfile;print(tempfile.mkdtemp(prefix="uit-preview-"))'])
  if (made.exitCode !== 0) {
    throw new Error(`python3 is needed for the preview server: ${made.stderr.trim() || 'it did not run'}`)
  }
  const dir = made.stdout.trim()

  let stillUri = ''
  try {
    const { base64 } = await $.fs.read(`${$.plugin.root}/assets/campus-night.png`, { as: 'bytes' })
    stillUri = `data:image/png;base64,${base64}`
  } catch {
    // The gallery shows the animated scenes without the still picture.
  }

  for (const theme of THEMES) {
    if (theme.scene) {
      await $.fs.write(`${dir}/${theme.id}.svg`, theme.scene.svg)
    }
  }
  await $.fs.write(
    `${dir}/index.html`,
    previewPage({
      current,
      stillUri,
      themes: THEMES.map(theme => ({
        id: theme.id,
        title: theme.title,
        blurb: theme.blurb,
        anchors: (theme.palette.dark ?? theme.palette.light)!.gray!.anchors as Record<string, string>,
        roles: theme.palette.roles as Record<string, string>,
        tint: theme.scene?.tint ?? '#04102a',
        opacity: theme.scene?.opacity ?? 0.72,
        kind: theme.scene ? 'scene' : theme.still ? 'still' : 'plain',
        gradient: theme.gradient ? [...theme.gradient] : undefined,
      })),
    }),
  )

  const stream = $.process.spawn({ argv: ['python3', '-u', '-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', dir] })

  const url = await new Promise<string>((resolve, reject) => {
    let said = ''
    let settled = false
    void (async () => {
      try {
        for await (const piece of stream) {
          if (settled) {
            continue
          }
          said += piece.text
          const port = /port (\d+)/.exec(said)?.[1]
          if (port) {
            settled = true
            resolve(`http://127.0.0.1:${port}/`)
          }
        }
        if (!settled) {
          reject(new Error(`the preview server stopped before it started: ${said.trim().slice(-300)}`))
        }
      } catch (error) {
        if (!settled) {
          reject(error instanceof Error ? error : new Error(String(error)))
        }
      } finally {
        if (server?.dir === dir) {
          server = undefined
        }
      }
    })()
  })

  server = { url, dir, stop: () => void stream.return(undefined as never) }

  return url
}

// ---------------------------------------------------------------- hooks
export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    for (const theme of THEMES) {
      const unpainted = COLORS.get(theme.id)!.problems.find(line => line.startsWith("Desktop won't paint"))
      if (unpainted !== undefined) {
        $.ui.toast(`${theme.title}: ${unpainted}`)
      }
    }

    await $.command.register({ name: 'uit', description: 'UIT themes: /uit <navy|monsoon|metro|silicon|tet|trungthu|exam|dawn|still|plain>, next, list, off' })
    await $.command.register({ name: 'uit-preview', description: 'Open a localhost gallery of the UIT theme scenes (/uit-preview stop ends it)' })

    const current = await currentId($)
    if (current !== 'off') {
      await $.theme.set(lookFor(findTheme(current) ?? THEMES[0]!))
    }

    return next(e)
  })

  on('command.run', { command: 'uit' }, async ($, e) => {
    const arg = e.args.trim().toLowerCase()
    const current = await currentId($)

    if (arg === '' || arg === 'list' || arg === 'help') {
      const state = current === 'off' ? 'UIT themes are off.' : `UIT theme: ${current}.`
      return { text: `${state}\n\n${listing(current)}\n\n${USAGE}` }
    }

    if (arg === 'off') {
      await $.store.set(STORE_KEY, 'off')
      await $.theme.clear()
      return { text: 'UIT themes are off. /uit navy turns them back on.' }
    }

    if (arg === 'preview' || arg === 'preview stop') {
      return previewCommand($, arg === 'preview' ? '' : 'stop', current)
    }

    let theme = findTheme(arg)
    if (arg === 'next') {
      const at = THEMES.findIndex(t => t.id === current)
      theme = THEMES[(at + 1) % THEMES.length]
    }
    if (!theme) {
      return { text: `Unknown theme "${arg}".\n\n${listing(current)}\n\n${USAGE}` }
    }

    await $.store.set(STORE_KEY, theme.id)
    const set = await $.theme.set(lookFor(theme))

    return {
      text: set.isDrawn
        ? `UIT theme: ${theme.title}. ${theme.blurb}.`
        : `UIT theme ${theme.title} saved, but nothing draws it here: ${set.reason}`,
    }
  })

  on('command.run', { command: 'uit-preview' }, async ($, e) => previewCommand($, e.args.trim().toLowerCase(), await currentId($)))

  on('ui.render', { component: 'Backdrop' }, ($, e, next) => {
    if (e.surface !== 'desktop' && e.surface !== 'mobile') {
      return next(e)
    }
    const theme = e.props.plugin === PLUGIN ? THEMES.find(t => t.scene && sceneName(t) === e.props.scene) : undefined
    if (!theme?.scene) {
      return next(e)
    }

    const { Svg } = $.ui.resolve(e)

    return <Svg source={theme.scene.svg} alt={theme.scene.alt} isInteractive />
  })
}

async function currentId($: Engine): Promise<string> {
  const stored = await $.store.get(STORE_KEY)
  if (stored === 'off' || (typeof stored === 'string' && findTheme(stored))) {
    return stored === 'off' ? 'off' : findTheme(stored)!.id
  }
  // Earlier versions kept scene | still | plain | off under 'variant'.
  const legacy = await $.store.get(LEGACY_KEY)
  if (legacy === 'off') {
    return 'off'
  }

  return typeof legacy === 'string' && findTheme(legacy) ? findTheme(legacy)!.id : 'navy'
}

async function previewCommand($: Engine, arg: string, current: string) {
  if (arg === 'stop') {
    if (!server) {
      return { text: 'No UIT preview server is running.' }
    }
    const { url } = server
    server.stop()
    server = undefined
    return { text: `Stopped the UIT preview server at ${url}` }
  }

  try {
    const wasRunning = server !== undefined
    const url = await startPreview($, current)
    // Open it in the default browser on macOS; elsewhere the link is enough.
    await $.process.run(['open', url]).catch(() => undefined)
    return {
      text: `${wasRunning ? 'UIT preview is already running' : 'UIT preview is up'}: ${url}\nLeft and right arrow keys switch scenes, G toggles the chat glass. /uit-preview stop ends it.`,
    }
  } catch (error) {
    return { text: `Could not start the UIT preview: ${error instanceof Error ? error.message : String(error)}` }
  }
}
