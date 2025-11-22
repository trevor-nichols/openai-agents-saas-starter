import { defineConfig, globalIgnores } from "eslint/config";
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
  nextIgnores,
  globalIgnores([
    "lib/api/client/**/*",
    ".next/**/*",
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
