/**
 * ESLint Flat Config for the repository (JavaScript only)
 * Uses @eslint/js recommended rules and eslint-plugin-import for ordering
 */
import js from "@eslint/js";
import pluginImport from "eslint-plugin-import";

export default [
  {
    ignores: [
      "**/node_modules/**",
      "dist/**",
      "build/**",
      "**/*.min.js",
      ".git/**"
    ]
  },
  {
    files: ["**/*.js", "**/*.cjs", "**/*.mjs"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        console: "readonly",
        process: "readonly",
        __dirname: "readonly",
        module: "readonly",
        require: "readonly",
        exports: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly"
      }
    },
    plugins: {
      import: pluginImport
    },
    rules: {
      ...js.configs.recommended.rules,
      "no-unused-vars": ["error", { "argsIgnorePattern": "^_", "varsIgnorePattern": "^_" }],
      "no-console": "off",
      "import/order": [
        "warn",
        {
          "newlines-between": "always",
          "groups": [["builtin", "external"], ["internal", "parent", "sibling", "index"]],
          "alphabetize": { "order": "asc", "caseInsensitive": true }
        }
      ],
      "import/newline-after-import": ["warn", { "count": 1 }]
    }
  }
];
