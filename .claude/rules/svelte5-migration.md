---
paths:
    - "ts/**/*.svelte"
---

# Svelte 5 Rules

Svelte 5 supports old Svelte 4 syntax too, but always prefer Svelte 5 syntax below unless the codebase is explicitly Svelte 4.

## Reactivity (Runes)

- `let x = 0` at top level → `let x = $state(0)`. Still read/write directly, no `.value`.
- `$: y = x * 2` (derivation) → `const y = $derived(x * 2)`.
- `$: { ... }` (side effect) → `$effect(() => { ... })`.
- `export let prop` → destructure from `$props()`: `let { optional = 'unset', required } = $props();`
  - Rename: `let { class: klass } = $props();`
  - Rest props: `let { foo, ...rest } = $props();`
  - All props: `let props = $props();`
- Bindable props require `$bindable()`: `let { foo = $bindable('bar') } = $props();`. Bind consumer must pass a defined value if using a default.
- Classes are not auto-reactive. Define `$state` fields inside the class itself; wrapping `new Foo()` in `$state()` does nothing.

## Events

- `on:click={fn}` → `onclick={fn}` (property, not directive, no colon).
- Shorthand works: `<button {onclick}>`.
- No event modifiers (`|once|preventDefault`). Handle inside the function or use wrapper functions (`once(fn)`, `preventDefault(fn)`).
- `capture` modifier → append to event name: `onclickcapture={...}`.
- `passive`/`nonpassive` → use an action, rarely needed.
- Duplicate handlers not allowed (`onclick={one} onclick={two}` invalid). Combine into one function.
- When spreading props, local handlers go after the spread or they get overwritten.
- `ontouchstart`/`ontouchmove` are passive by default now. Use `on` from `svelte/events` if you truly need `preventDefault`.
- `oneventname="string"` (inline string handler) is no longer valid, must be a function reference.

## Component Events (replace createEventDispatcher)

- `createEventDispatcher` is deprecated. Use callback props instead.
- Child: `let { inflate, deflate } = $props();` then call `inflate(power)` directly (no `.detail` wrapper).
- Parent: pass functions as props, e.g. `<Pump inflate={(power) => {...}} />`.
- Bubbling: child accepts `let { onclick } = $props();` and does `<button {onclick}>`.

## Snippets (replace slots)

- Slots still work but are deprecated; prefer snippets for new code.
- Default slot → `children` prop: `let { children } = $props();` then `{@render children?.()}`.
- Named slots → named snippet props: `let { header, main, footer } = $props();` then `{@render header()}`.
- Passing data back up (`let:item`) → snippet params: `{#snippet item(text)}...{/snippet}` and child does `{@render item(entry)}`.
- `children` is a reserved prop name, cannot be redefined for other purposes.
- Cannot pass slotted content into a component that only uses `{@render}` tags.

## Components Are Functions, Not Classes

- Instantiate with `mount` or `hydrate` from `svelte`, not `new Component(...)`.
  ```js
  import { mount } from "svelte";
  const app = mount(App, { target: document.getElementById("app") });
  ```
- `$on` → pass `events` option to `mount` (discouraged, prefer callback props).
- `$set` → use `$state` for props object, then mutate it directly.
  ```js
  const props = $state({ foo: "bar" });
  const app = mount(App, { target, props });
  props.foo = "baz";
  ```
- `$destroy` → `unmount(app)` from `svelte`.
- `mount`/`hydrate` are async (not synchronous like `new Component()`). Use `flushSync` from `svelte` if you need synchronous behavior right after.
- Server render: `Component.render(...)` → `render(Component, { props })` imported from `svelte/server`.
- SSR no longer returns CSS by default. Set compiler option `css: 'injected'` if needed.
- Type `SvelteComponent` → `Component` type from `svelte`. `ComponentEvents`/`ComponentType` deprecated.
- `bind:this` no longer gives `$set`/`$on`/`$destroy`, only instance exports and accessor getters/setters (if `accessors: true`).
- Cannot `bind:` to component exports (`export const foo`). Use `bind:this` and access `instance.foo` instead.
- `accessors` compiler option is ignored in runes mode. Expose values via component exports instead.
- `immutable` compiler option is ignored in runes mode.

## Dynamic Components

- `<svelte:component this={Thing}>` is no longer necessary. Just use `<Thing />` directly; it updates reactively when `Thing` changes.
- Capitalize component variable names to distinguish from elements.
- `<foo.bar>` is now treated as a component (dot notation), not a literal element tag. Useful in `{#each}` blocks: `<item.component {...item.props} />`.

## Whitespace

- Whitespace between nodes collapses to a single space.
- Whitespace at start/end of a tag is fully removed.
- `<p>foo<span> - bar</span></p>` renders as `foo- bar` (not `foo - bar` like HTML). Fix by moving space outside the tag or using `{' '}`.
- `preserveWhitespace` compiler option / `<svelte:options>` still available to opt out.

## Removed / Changed Compiler Options

- `hydratable` removed (always hydratable now).
- `enableSourcemap` removed (always generated).
- `tag` removed, use `<svelte:options customElement="tag-name" />`.
- `loopGuardTimeout`, `format`, `sveltePath`, `errorMode`, `varsReport` all removed.
- `legacy` option repurposed (no longer means IE support; IE is not supported at all).
- `css` option no longer accepts `false`/`true`/`"none"`.

## Other Breaking Changes

- `@const` destructured assignment no longer allowed.
- `beforeUpdate`/`afterUpdate`: disallowed in runes mode, use `$effect.pre(...)` / `$effect(...)`. Also: no longer double-runs on initial render, parent `afterUpdate` now runs after child's, doesn't run for `<slot>` content updates.
- `contenteditable` with a binding and reactive value inside: the binding takes over, reactive updates to the value no longer touch the DOM content.
- `bind:files` must be `null`, `undefined`, or `FileList`, nothing else.
- Bindings now respond to native form `reset` events.
- Stricter attribute quoting: unquoted complex values like `prop=this{is}valid` are invalid. Must quote: `prop="this{is}valid"`. Conversely a lone expression in quotes like `answer="{42}"` will warn (converts to string in Svelte 6).
- Stricter HTML structure: no relying on browser auto-repair (e.g. missing `<tbody>` in `<table>`), compiler now errors.
