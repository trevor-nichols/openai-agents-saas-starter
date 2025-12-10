export function usePlatformStatusQuery() {
  return {
    status: {
      generatedAt: new Date().toISOString(),
      overview: { state: 'Operational', description: 'All systems go', updatedAt: new Date().toISOString() },
      services: [],
      incidents: [],
      uptimeMetrics: [],
    },
    isLoading: false,
    error: null,
    refetch: () => {},
  };
}
