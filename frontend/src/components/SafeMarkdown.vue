<script setup lang="ts">
import { computed, ref } from 'vue'
import { copyText } from '../utils/clipboard'
type Block = { type: 'heading'; level: number; text: string } | { type: 'paragraph'; text: string } | { type: 'list'; ordered: boolean; items: string[] } | { type: 'code'; text: string; language: string }
const props = defineProps<{ source: string }>()
const copied = ref<number | null>(null)
const inlineParts = (text: string) => text.split(/(`[^`]+`)/g).filter(Boolean).map(value => ({ text: value.startsWith('`') && value.endsWith('`') ? value.slice(1, -1) : value, code: value.startsWith('`') && value.endsWith('`') }))
const blocks = computed<Block[]>(() => {
  const result: Block[] = [], lines = props.source.replace(/\r\n/g, '\n').split('\n')
  let paragraph: string[] = [], list: string[] = [], ordered = false, code: string[] | null = null, language = ''
  const flushParagraph = () => { if (paragraph.length) result.push({ type: 'paragraph', text: paragraph.join(' ') }); paragraph = [] }
  const flushList = () => { if (list.length) result.push({ type: 'list', ordered, items: [...list] }); list = [] }
  const flushCode = () => { if (code !== null) result.push({ type: 'code', text: code.join('\n'), language }); code = null; language = '' }
  for (const rawLine of lines) {
    const line = rawLine.trimEnd(), fence = /^```\s*([^\s]*)/.exec(line)
    if (fence) { flushParagraph(); flushList(); if (code === null) { code = []; language = fence[1] ?? '' } else flushCode(); continue }
    if (code !== null) { code.push(rawLine); continue }
    const heading = /^(#{1,4})\s+(.+)$/.exec(line)
    if (heading) { flushParagraph(); flushList(); result.push({ type: 'heading', level: heading[1]?.length ?? 2, text: heading[2] ?? '' }); continue }
    const item = /^\s*(?:(\d+)\.|[-*])\s+(.+)$/.exec(line)
    if (item) { flushParagraph(); const nextOrdered = Boolean(item[1]); if (list.length && ordered !== nextOrdered) flushList(); ordered = nextOrdered; list.push(item[2] ?? ''); continue }
    if (!line.trim()) { flushParagraph(); flushList(); continue }
    flushList(); paragraph.push(line.trim())
  }
  flushParagraph(); flushList(); if (code !== null) flushCode(); return result
})
async function copyBlock(index: number, text: string) { await copyText(text); copied.value = index; window.setTimeout(() => { if (copied.value === index) copied.value = null }, 1800) }
</script>
<template>
  <div class="safe-markdown">
    <template v-for="(block, index) in blocks" :key="index">
      <h2 v-if="block.type === 'heading' && block.level <= 2" class="text-h6 mt-6 mb-3">{{ block.text }}</h2>
      <h3 v-else-if="block.type === 'heading'" class="text-subtitle-1 font-weight-bold mt-5 mb-2">{{ block.text }}</h3>
      <p v-else-if="block.type === 'paragraph'" class="markdown-paragraph"><template v-for="(part, i) in inlineParts(block.text)" :key="i"><code v-if="part.code" class="inline-code">{{ part.text }}</code><template v-else>{{ part.text }}</template></template></p>
      <component :is="block.ordered ? 'ol' : 'ul'" v-else-if="block.type === 'list'" class="markdown-list"><li v-for="item in block.items" :key="item"><template v-for="(part, i) in inlineParts(item)" :key="i"><code v-if="part.code" class="inline-code">{{ part.text }}</code><template v-else>{{ part.text }}</template></template></li></component>
      <details v-else-if="block.type === 'code'" class="code-window" :open="block.text.split('\n').length <= 8">
        <summary class="code-header"><span><v-icon icon="mdi-code-tags" size="small" /> {{ block.language || 'Code' }}</span><v-btn size="x-small" variant="text" prepend-icon="mdi-content-copy" @click.prevent.stop="copyBlock(index, block.text)">{{ copied === index ? 'Kopiert' : 'Kopieren' }}</v-btn></summary>
        <pre><code>{{ block.text }}</code></pre>
      </details>
    </template>
  </div>
</template>
<style scoped>
.safe-markdown { line-height: 1.7; max-width: 100%; }.markdown-paragraph { margin: 0 0 1rem; max-width: 78ch; }.markdown-list { margin: 0 0 1.15rem; padding-left: 1.7rem; }.markdown-list li { margin-bottom: .4rem; }.inline-code { padding: .12rem .35rem; border-radius: 5px; background: rgba(var(--v-theme-on-surface), .08); font-size: .92em; overflow-wrap: anywhere; }.code-window { margin: 0 0 1.25rem; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 10px; background: rgba(var(--v-theme-on-surface), .04); overflow: hidden; }.code-header { display: flex; align-items: center; justify-content: space-between; min-height: 42px; padding: .25rem .5rem .25rem .8rem; cursor: pointer; background: rgba(var(--v-theme-on-surface), .06); font-family: monospace; }.code-window pre { overflow: auto; max-height: 32rem; margin: 0; padding: 1rem; white-space: pre; }
</style>
