#!/usr/bin/env node
import { execFileSync } from 'node:child_process'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { createRequire } from 'node:module'
import { join, relative, resolve } from 'node:path'

const root = resolve(new URL('..', import.meta.url).pathname)
const require = createRequire(import.meta.url)
const globalRoot = execFileSync('npm', ['root', '-g'], { encoding: 'utf8' }).trim()
const ts = require(join(globalRoot, 'typescript'))

function walk(directory) {
  const result = []
  for (const name of readdirSync(directory)) {
    const path = join(directory, name)
    const stat = statSync(path)
    if (stat.isDirectory()) {
      if (!['node_modules', 'dist', '.git'].includes(name)) result.push(...walk(path))
    } else {
      result.push(path)
    }
  }
  return result
}

const diagnostics = []
let units = 0
function check(source, filename) {
  units += 1
  const sourceFile = ts.createSourceFile(
    filename,
    source,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TS
  )
  for (const diagnostic of sourceFile.parseDiagnostics ?? []) {
    if (diagnostic.category !== ts.DiagnosticCategory.Error) continue
    const position = diagnostic.start === undefined
      ? ''
      : (() => {
          const location = sourceFile.getLineAndCharacterOfPosition(diagnostic.start)
          return `:${location.line + 1}:${location.character + 1}`
        })()
    diagnostics.push(
      `${relative(root, filename)}${position}: ${ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')}`
    )
  }
}

for (const file of walk(join(root, 'frontend', 'src'))) {
  if (file.endsWith('.ts')) {
    check(readFileSync(file, 'utf8'), file)
  } else if (file.endsWith('.vue')) {
    const content = readFileSync(file, 'utf8')
    const match = content.match(/<script\s+setup(?:\s+lang=["']ts["'])?[^>]*>([\s\S]*?)<\/script>/)
    if (match) check(match[1], `${file}.ts`)
  }
}

if (diagnostics.length) {
  console.error(diagnostics.join('\n'))
  process.exit(1)
}
console.log(`${units} TypeScript-/Vue-Skripteinheiten syntaktisch geprüft.`)
