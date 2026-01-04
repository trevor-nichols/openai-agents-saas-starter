import { defineConfig, globalIgnores } from "eslint/config";
import boundaries from "eslint-plugin-boundaries";
import nextConfig from "eslint-config-next";

const [nextBase, nextTypescript, nextIgnores] = nextConfig;

const eslintConfig = defineConfig([
  {
    ...nextBase,
    rules: {
      ...nextBase.rules,
      "react-hooks/incompatible-library": "off",
    },
  },
  {
    ...nextTypescript,
    rules: {
      ...(nextTypescript.rules ?? {}),
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],
    },
  },
  {
    files: ["app/api/**/route.ts", "app/api/**/route.tsx"],
    plugins: {
      boundaries,
    },
    settings: {
      "boundaries/elements": [
        { type: "bff-route", pattern: "app/api/**/route.*" },
        { type: "api-client", pattern: "lib/api/client/**" },
        { type: "server-config", pattern: "lib/config/server.*" },
        { type: "server-api-client", pattern: "lib/server/apiClient.*" },
      ],
    },
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: [
                "@/lib/api/client",
                "@/lib/api/client/*",
                "lib/api/client",
                "lib/api/client/*",
              ],
              allowTypeImports: true,
              message:
                "BFF routes must call server services; do not import the generated SDK.",
            },
            {
              group: ["@/lib/config/server", "lib/config/server"],
              message:
                "BFF routes must not access API_BASE_URL directly; use server services instead.",
            },
            {
              group: ["@/lib/server/apiClient", "lib/server/apiClient"],
              message:
                "BFF routes must call server services; do not import server apiClient directly.",
            },
          ],
        },
      ],
      "boundaries/element-types": [
        "error",
        {
          default: "allow",
          rules: [
            {
              from: "bff-route",
              disallow: ["api-client", "server-config", "server-api-client"],
              importKind: "value",
            },
          ],
        },
      ],
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.name='fetch']",
          message:
            "BFF routes must call server services; do not call fetch directly.",
        },
      ],
    },
  },
  nextIgnores,
  globalIgnores([
    "lib/api/client/**/*",
    ".next/**/*",
    ".next-mock/**/*",
    "node_modules/**/*",
    "next-env.d.ts",
    "pnpm-lock.yaml",
    "package-lock.json",
    "storybook-static/**/*",
    ".storybook/**/*.cjs",
    ".storybook/**/*.js",
  ]),
]);

export default eslintConfig;
