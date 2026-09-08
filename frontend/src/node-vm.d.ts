// Minimal Node test-runtime declarations; no Node APIs ship in the browser bundle.
declare module 'node:vm' {
  export function createContext(context: object): object
  export function runInContext(code: string, context: object): any
}
