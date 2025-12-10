export function useTools() {
  return {
    tools: {
      file_search: { description: 'Search files', name: 'file_search' },
      web_search: { description: 'Search the web', name: 'web_search' },
      browser: { description: 'Headful browser', name: 'browser' },
    },
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}
