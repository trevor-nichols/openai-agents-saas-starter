export function useAgents() {
  return {
    agents: [
      { name: 'triage_agent', display_name: 'Triage Agent', description: 'Routes requests', status: 'active', model: 'gpt-5.1', last_seen_at: new Date().toISOString() },
      { name: 'research_agent', display_name: 'Research Agent', description: 'Deep dives docs', status: 'active', model: 'gpt-5.1', last_seen_at: new Date().toISOString() },
    ],
    isLoadingAgents: false,
    agentsError: null,
  };
}
