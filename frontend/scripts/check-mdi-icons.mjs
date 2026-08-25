import { readFileSync, readdirSync } from 'node:fs'
import { dirname, extname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendRoot = dirname(dirname(fileURLToPath(import.meta.url)))
const sourceRoot = join(frontendRoot, 'src')
const iconCssPath = join(
  frontendRoot,
  'node_modules',
  '@mdi',
  'font',
  'css',
  'materialdesignicons.css'
)
const iconCss = readFileSync(iconCssPath, 'utf8')
const sourceExtensions = new Set(['.ts', '.vue'])
const usedIcons = new Set()

function scan(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    if (entry.isDirectory()) {
      scan(path)
      continue
    }
    if (!sourceExtensions.has(extname(entry.name))) continue
    const matches = readFileSync(path, 'utf8').match(/mdi-[a-z0-9-]+/g) ?? []
    matches.forEach((icon) => usedIcons.add(icon))
  }
}

scan(sourceRoot)
const missingIcons = [...usedIcons]
  .filter((icon) => !iconCss.includes(`.${icon}::before`))
  .sort()

if (missingIcons.length > 0) {
  throw new Error(`Nicht verfügbare MDI-Icons: ${missingIcons.join(', ')}`)
}

console.log(`${usedIcons.size} MDI-Icons geprüft: alle verfügbar.`)
