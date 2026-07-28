import globals from "globals";

export default [
  {
    files: ["js/**/*.js"],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
      ecmaVersion: 2022,
      sourceType: "module",
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": "off",
      "eqeqeq": "error",
      "no-var": "error",
      "prefer-const": "error",
      "semi": ["error", "always"],
      "quotes": ["error", "double"],
    },
  },
];
