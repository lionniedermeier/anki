# Migrating a PyQt view to Svelte

Anki is incrementally moving user-facing views from native PyQt widgets to
Svelte pages rendered inside an `AnkiWebView`. Because a migrated view is just a
webview embedded in the existing PyQt window, Svelte and PyQt screens coexist and
each view can be migrated independently.

This page documents the recipe. The **deck chooser** and **deck description**
views are the reference implementations:

- `ts/routes/deck-chooser/[deckId]/` and `qt/aqt/deckchooser.py`
- `ts/routes/deck-description/[deckId]/` and `qt/aqt/deckdescription.py`

## How the pieces fit together

- The PyQt class creates an `AnkiWebView` and points it at a SvelteKit route with
  `load_sveltekit_page(...)`.
- The route's `+page.ts` `load()` fetches its initial data from the backend over
  HTTP (protobuf) via `@generated/backend`.
- Writes go straight to the backend from Svelte (also via `@generated/backend`) —
  they do **not** go through the Qt `operations` pipeline.
- Two-way UI signalling uses the bridge:
  - **Svelte → Python:** `bridgeCommand("some-command")`.
  - **Python → Svelte:** `web.eval("window.updateX(...)")`, guarded so it is a
    no-op if the function is not defined yet.

## Recipe

### 1. Create the Svelte route

Under `ts/routes/<name>/[...params]/`:

**`+page.ts`** — load initial data:

```ts
import { getDeck } from "@generated/backend";
import type { PageLoad } from "./$types";

export const load = (async ({ params }) => {
    const did = BigInt(params.deckId);
    const deck = await getDeck({ did });
    return { deck };
}) satisfies PageLoad;
```

Note `BigInt(...)` for id params — Anki ids are 64-bit.

**`+page.svelte`** — render with the shared components in `ts/lib/components/`,
write via `@generated/backend`, signal Python with `bridgeCommand`, and expose a
`window.*` callback for Python-pushed updates:

```svelte
<script lang="ts">
    import { updateDeck } from "@generated/backend";
    import { bridgeCommand } from "@tslib/bridgecommand";
    import { onMount } from "svelte";
    import type { PageData } from "./$types";

    export let data: PageData;

    onMount(() => {
        (window as any).updateX = (value: string) => { /* ... */ };
        return () => { delete (window as any).updateX; };
    });

    async function save(): Promise<void> {
        await updateDeck(data.deck);   // write directly to the backend
        bridgeCommand("close");        // tell the Python host we're done
    }
</script>
```

### 2. Rework the PyQt class

Replace the native widgets with an `AnkiWebView`:

```python
from aqt.webview import AnkiWebView, AnkiWebViewKind

self.web = AnkiWebView(kind=AnkiWebViewKind.DECK_DESCRIPTION)
self.web.set_bridge_command(self._on_bridge_cmd, self)
self.web.load_sveltekit_page(f"deck-description/{self._deck_id}")
```

Handle the commands the page emits. If a handler tears down the webview (e.g.
closing the dialog), defer it so the view is not destroyed from inside its own
callback:

```python
def _on_bridge_cmd(self, cmd: str) -> None:
    if cmd == "close":
        QTimer.singleShot(0, self.close)
```

Push updates to the page with `web.eval`, guarding the call:

```python
name = json.dumps(self.selected_deck_name())
self.web.eval(f"typeof updateX === 'function' && updateX({name});")
```

Always clean up the webview when the view goes away:

```python
def cleanup(self) -> None:
    if self.web and not sip.isdeleted(self.web):
        self.web.cleanup()
        self.web = None  # type: ignore
```

Because writes bypass the Qt operations pipeline, refresh the surrounding UI
after the dialog closes (e.g. `self.mw.reset()`) so the change becomes visible.

### 3. Register the view kind (`qt/aqt/webview.py`)

Add a value to `AnkiWebViewKind`, and add it to the tuple of kinds granted
backend API access in `AnkiWebPage`.

### 4. Register the route and RPCs (`qt/aqt/mediasrv.py`)

- Add `<name>` to the list in `is_sveltekit_page()` (matched on the first path
  segment, so route params don't matter).
- Add any backend RPCs the page calls to `exposed_backend_list` (e.g. `get_deck`,
  `update_deck`). Most views reuse existing RPCs.

### 5. Protobuf (only if needed)

Only touch `proto/anki/` when the page needs a genuinely new backend RPC. The
deck views reused the existing `get_deck`/`update_deck` RPCs and needed no proto
changes. Adding a proto method requires a full build (`just check`).

## Testing

- `just check` runs formatting, the build, lints, and type checks
  (`check:svelte`, `check:typescript`, `check:mypy`, `check:ruff`).
- Registration is guarded by `TestIsSveltekitPage` / `TestExposedBackend` in
  `qt/tests/test_mediasrv.py` — extend the parametrized lists when adding a view.
- For pages with non-trivial logic, factor it into a `lib.ts` and unit-test it as
  `deck-options` does (`ts/routes/deck-options/lib.test.ts`).
- End-to-end coverage lives in `ts/tests/e2e/` (`just test-e2e`).
