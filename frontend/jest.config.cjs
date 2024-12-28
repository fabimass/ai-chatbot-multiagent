module.exports = {
  preset: "ts-jest",
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["./src/setupTests.ts"],
  moduleNameMapper: {
    "\\.(jpg|jpeg|png|gif|webp|svg)$": "<rootDir>/mocks/fileMock.js", // To mock image imports
    "^@/(.*)$": "<rootDir>/src/$1", // Map `@/` to the `src/` directory
  },
};
