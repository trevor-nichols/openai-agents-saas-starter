export function getSelectedProjects(argv: string[]): Set<string> | null {
  const selected = new Set<string>();
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!arg) {
      continue;
    }
    if (arg.startsWith('--project=')) {
      const value = arg.split('=')[1];
      if (value) selected.add(value);
    } else if (arg === '--project' || arg === '-p') {
      const nextArg = argv[index + 1];
      if (nextArg) {
        selected.add(nextArg);
        index += 1;
      }
    }
  }
  return selected.size ? selected : null;
}

export function shouldRunProject(selected: Set<string> | null, projectName: string): boolean {
  if (!selected) {
    return true;
  }
  return selected.has(projectName);
}
