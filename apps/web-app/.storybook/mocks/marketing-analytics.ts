export function useMarketingAnalytics() {
  return {
    trackLeadSubmit: (payload: unknown) => {
      console.log('track lead submit', payload);
    },
  };
}
