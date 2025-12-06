import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { WorkflowGraph } from '../WorkflowGraph';
import type { WorkflowDescriptor } from '@/lib/workflows/types';

// Minimal ResizeObserver polyfill for layout-dependent components
class ResizeObserverMock {
  observe() {}
  disconnect() {}
}
(global as any).ResizeObserver = ResizeObserverMock;

const beamSpy: any[] = [];

vi.mock('@/components/ui/beam', () => ({
  AnimatedBeam: (props: any) => {
    beamSpy.push(props);
    return <div data-testid="beam" data-animated={props.animated ? 'true' : 'false'} />;
  },
}));

const descriptor: WorkflowDescriptor = {
  key: 'demo',
  display_name: 'Demo Workflow',
  description: 'Demo',
  default: false,
  allow_handoff_agents: false,
  step_count: 4,
  output_schema: null,
  stages: [
    {
      name: 'collect',
      mode: 'sequential',
      reducer: null,
      steps: [
        { name: 'Collect Input', agent_key: 'agent-collect', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Summarize', agent_key: 'agent-summarize', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
    {
      name: 'notify',
      mode: 'parallel',
      reducer: null,
      steps: [
        { name: 'Notify A', agent_key: 'agent-a', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Notify B', agent_key: 'agent-b', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
  ],
};

describe('WorkflowGraph', () => {
  beforeEach(() => {
    beamSpy.length = 0;
  });

  it('renders steps from the descriptor', () => {
    render(<WorkflowGraph descriptor={descriptor} />);

    expect(screen.getByText('Collect Input')).toBeInTheDocument();
    expect(screen.getByText('Summarize')).toBeInTheDocument();
    expect(screen.getByText('Notify A')).toBeInTheDocument();
    expect(screen.getByText('Notify B')).toBeInTheDocument();
  });

  it('highlights the active step and animates only its incoming beam', () => {
    render(
      <WorkflowGraph
        descriptor={descriptor}
        activeStep={{ stepName: 'Notify A', stageName: 'notify', parallelGroup: 'notify', branchIndex: 0 }}
      />,
    );

    const label = screen.getByText('Notify A');
    let cursor: HTMLElement | null = label.closest('div');
    let foundHighlighted = false;
    while (cursor) {
      if (cursor.className?.includes('ring-2')) {
        foundHighlighted = true;
        break;
      }
      cursor = cursor.parentElement;
    }
    expect(foundHighlighted).toBe(true);

    const animatedBeams = beamSpy.filter((b) => b.animated);
    const staticBeams = beamSpy.filter((b) => !b.animated);

    expect(animatedBeams.length).toBe(1);
    expect(staticBeams.length).toBeGreaterThan(0);
  });

  it('matches active step by name when stage is missing', () => {
    render(
      <WorkflowGraph
        descriptor={descriptor}
        activeStep={{ stepName: 'Summarize', stageName: null, parallelGroup: null, branchIndex: null }}
      />,
    );

    const label = screen.getByText('Summarize');
    let cursor: HTMLElement | null = label.closest('div');
    let foundHighlighted = false;
    while (cursor) {
      if (cursor.className?.includes('ring-2')) {
        foundHighlighted = true;
        break;
      }
      cursor = cursor.parentElement;
    }
    expect(foundHighlighted).toBe(true);

    const animatedBeams = beamSpy.filter((b) => b.animated);
    expect(animatedBeams.length).toBe(1);
  });

  it('matches by parallel group when names are absent', () => {
    render(
      <WorkflowGraph
        descriptor={descriptor}
        activeStep={{ stepName: null, stageName: null, parallelGroup: 'notify', branchIndex: 1 }}
      />,
    );

    const label = screen.getByText('Notify B');
    let cursor: HTMLElement | null = label.closest('div');
    let foundHighlighted = false;
    while (cursor) {
      if (cursor.className?.includes('ring-2')) {
        foundHighlighted = true;
        break;
      }
      cursor = cursor.parentElement;
    }
    expect(foundHighlighted).toBe(true);

    const animatedBeams = beamSpy.filter((b) => b.animated);
    expect(animatedBeams.length).toBe(1);
  });
});
