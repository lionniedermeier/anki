import js from "@eslint/js";
import compat from "eslint-plugin-compat";
import importPlugin from "eslint-plugin-import";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
    {
        ignores: [
            "**/backend_proto.d.ts",
            "**/*.svelte.d.ts",
            "**/vendor/**",
            "**/extra/**",
            "**/vite.config.ts",
            "**/hooks.client.js",
            "**/.svelte-kit/**",
            "**/out/**",
        ],
    },
    js.configs.recommended,
    {
        files: ["**/*.ts"],
        extends: [...tseslint.configs.recommended],
    },
    compat.configs["flat/recommended"],
    ...svelte.configs.recommended,
    {
        ignores: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
        languageOptions: {
            parser: tseslint.parser,
        },
    },
    {
        plugins: {
            import: importPlugin,
            "@typescript-eslint": tseslint.plugin,
        },
        languageOptions: {
            ecmaVersion: 2020,
            parserOptions: {
                extraFileExtensions: [".svelte"],
            },
            globals: {
                ...globals.browser,
                globalThis: false,
                NodeListOf: false,
                $$Generic: "readonly",
            },
        },
        rules: {
            "@typescript-eslint/ban-ts-comment": "warn",
            "@typescript-eslint/no-unused-vars": [
                "warn",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                    caughtErrorsIgnorePattern: "^_",
                },
            ],
            "no-unused-vars": "off",
            "import/newline-after-import": "warn",
            "import/no-useless-path-segments": "warn",
            "prefer-const": "warn",
            "no-nested-ternary": "warn",
            curly: "error",
            "@typescript-eslint/consistent-type-imports": "error",
        },
    },
    {
        files: ["**/*.mjs", "**/*.cjs"],
        languageOptions: {
            globals: {
                ...globals.node,
            },
        },
    },
    {
        files: ["**/*.ts"],
        rules: {
            "@typescript-eslint/no-non-null-assertion": "off",
            "@typescript-eslint/no-explicit-any": "off",
        },
    },
    {
        files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
        languageOptions: {
            parserOptions: {
                parser: tseslint.parser,
                svelteFeatures: {
                    experimentalGenerics: true,
                },
            },
        },
        rules: {
            "svelte/no-at-html-tags": "off",
            "svelte/valid-compile": ["error", { ignoreWarnings: true }],
            "@typescript-eslint/no-explicit-any": "off",
            "prefer-const": "off",
            // TODO: enable this when we're ready to absorb the churn
            // "svelte/prefer-const": "warn",
            "svelte/infinite-reactive-loop": "off",
            "svelte/no-dom-manipulating": "off",
            "svelte/no-dupe-on-directives": "off",
            "svelte/no-dupe-use-directives": "off",
            "svelte/no-export-load-in-svelte-module-in-kit-pages": "off",
            "svelte/no-immutable-reactive-statements": "off",
            "svelte/no-inspect": "off",
            "svelte/no-navigation-without-resolve": "off",
            "svelte/no-raw-special-elements": "off",
            "svelte/no-reactive-functions": "off",
            "svelte/no-reactive-literals": "off",
            "svelte/no-reactive-reassign": "off",
            "svelte/no-unnecessary-state-wrap": "off",
            "svelte/no-unused-props": "off",
            "svelte/no-useless-children-snippet": "off",
            "svelte/no-useless-mustaches": "off",
            "svelte/prefer-svelte-reactivity": "off",
            "svelte/prefer-writable-derived": "off",
            "svelte/require-each-key": "off",
            "svelte/require-event-dispatcher-types": "off",
            "svelte/valid-each-key": "off",
            "svelte/valid-prop-names-in-kit-pages": "off",
        },
    },
);
