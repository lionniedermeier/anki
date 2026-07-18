// Copyright: Ankitects Pty Ltd and contributors
// License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import { build } from "esbuild";
import { sassPlugin } from "esbuild-sass-plugin";
import sveltePlugin from "esbuild-svelte";
import { readFileSync, writeFileSync } from "fs";
import { basename } from "path";
import { argv, env } from "process";
import sveltePreprocess from "svelte-preprocess";
import { typescript } from "svelte-preprocess-esbuild";

const [_tsx, _script, entrypoint, bundle_js, bundle_css, page_html] = argv;

if (page_html != null) {
    const template = readFileSync("ts/page.html", { encoding: "utf8" });
    writeFileSync(page_html, template.replace(/{PAGE}/g, basename(page_html, ".html")));
}

// support Qt 5.14
const target = ["es2020", "chrome77"];
const inlineCss = bundle_css == null;
const sourcemap = env.SOURCEMAP && true;
let sveltePlugins;

// out/ts/lib/sass holds _tokens.scss, generated from tokens.json by
// gen_theme_tokens.py; Svelte component <style lang="scss"> blocks are
// compiled by svelte-preprocess, which needs its own includePaths entry to
// resolve @use "tokens" (separate from the esbuild-sass-plugin loadPaths
// below, which only cover .scss files imported directly by JS/TS).
const scssOptions = { includePaths: ["out/ts/lib/sass"] };

if (!sourcemap) {
    sveltePlugins = [
        // use esbuild for faster typescript transpilation
        typescript({
            target,
            define: {
                "process.browser": "true",
            },
            tsconfig: "ts/tsconfig_legacy.json",
        }),
        sveltePreprocess({ typescript: false, scss: scssOptions }),
    ];
} else {
    sveltePlugins = [
        // use tsc for more accurate sourcemaps
        sveltePreprocess({ typescript: true, sourceMap: true, scss: scssOptions }),
    ];
}

const ignoreCssUrlPlugin = {
    name: "ignore-css-url",
    setup(build) {
        // This works around esbuild unconditionally resolving CSS imports that uses Vite's `?url` syntax in the editor
        build.onResolve({ filter: /.*?\.scss\?url$/ }, (args) => {
            return { path: args.path, external: true };
        });
    },
};

build({
    bundle: true,
    entryPoints: [entrypoint],
    globalName: "anki",
    outfile: bundle_js,
    minify: env.RELEASE && true,
    loader: { ".svg": "text" },
    preserveSymlinks: true,
    sourcemap: sourcemap ? "inline" : false,

    plugins: [
        // out/ts/lib/sass holds _tokens.scss, generated from tokens.json by
        // gen_theme_tokens.py
        sassPlugin({ loadPaths: ["node_modules", "out/ts/lib/sass"] }),
        sveltePlugin({
            compilerOptions: { css: inlineCss ? "injected" : "external" },
            preprocess: sveltePlugins,
            // let us focus on errors; we can see the warnings with svelte-check
            filterWarnings: (_warning) => false,
        }),
        ignoreCssUrlPlugin,
    ],
    target,
    // logLevel: "info",
}).catch(() => process.exit(1));
