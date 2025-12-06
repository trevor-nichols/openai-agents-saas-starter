export function getLastModified(): Date {
  const fromGit = process.env.VERCEL_GIT_COMMIT_TIMESTAMP;
  if (fromGit) {
    const parsed = new Date(fromGit);
    if (!Number.isNaN(parsed.getTime())) {
      return parsed;
    }
  }

  return new Date();
}
