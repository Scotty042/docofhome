<script setup lang="ts">
import { computed } from 'vue'

type MarkdownBlock =
  | { type: 'heading'; level: number; text: string }
  | { type: 'paragraph'; text: string }
  | { type: 'list'; items: string[] }
  | { type: 'code'; text: string }

const props = defineProps<{ source: string }>()

const blocks = computed<MarkdownBlock[]>(() => {
  const result: MarkdownBlock[] = []
  const lines = props.source.replace(/\r\n/g, '\n').split('\n')
  let paragraph: string[] = []
  let list: string[] = []
  let code: string[] | null = null

  const flushParagraph = () => {
    if (paragraph.length) result.push({ type: 'paragraph', text: paragraph.join(' ') })
    paragraph = []
  }
  const flushList = () => {
    if (list.length) result.push({ type: 'list', items: [...list] })
    list = []
  }
  const flushCode = () => {
    if (code !== null) result.push({ type: 'code', text: code.join('\n') })
    code = null
  }

  for (const rawLine of lines) {
    const line = rawLine.trimEnd()
    if (line.startsWith('```')) {
      flushParagraph()
      flushList()
      if (code === null) code = []
      else flushCode()
      continue
    }
    if (code !== null) {
      code.push(rawLine)
      continue
    }
    const heading = /^(#{1,4})\s+(.+)$/.exec(line)
    if (heading) {
      flushParagraph()
      flushList()
      result.push({ type: 'heading', level: heading[1]?.length ?? 2, text: heading[2] ?? '' })
      continue
    }
    const item = /^[-*]\s+(.+)$/.exec(line)
    if (item) {
      flushParagraph()
      list.push(item[1] ?? '')
      continue
    }
    if (!line.trim()) {
      flushParagraph()
      flushList()
      continue
    }
    flushList()
    paragraph.push(line.trim())
  }
  flushParagraph()
  flushList()
  if (code !== null) flushCode()
  return result
})
</script>

<template>
  <div class="safe-markdown">
    <template v-for="(block, index) in blocks" :key="index">
      <h2 v-if="block.type === 'heading' && block.level <= 2" class="text-h6 mt-5 mb-2">
        {{ block.text }}
      </h2>
      <h3 v-else-if="block.type === 'heading'" class="text-subtitle-1 font-weight-bold mt-4 mb-2">
        {{ block.text }}
      </h3>
      <p v-else-if="block.type === 'paragraph'" class="mb-3">{{ block.text }}</p>
      <ul v-else-if="block.type === 'list'" class="mb-3 pl-6">
        <li v-for="item in block.items" :key="item" class="mb-1">{{ item }}</li>
      </ul>
      <pre v-else-if="block.type === 'code'" class="markdown-code"><code>{{ block.text }}</code></pre>
    </template>
  </div>
</template>

<style scoped>
.safe-markdown {
  line-height: 1.65;
}

.markdown-code {
  overflow-x: auto;
  margin: 0 0 1rem;
  padding: 0.9rem;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 10px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  white-space: pre-wrap;
}
</style>
