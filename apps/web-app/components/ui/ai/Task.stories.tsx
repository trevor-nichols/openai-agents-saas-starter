import type { Meta, StoryObj } from '@storybook/react';

import { Task, TaskContent, TaskItem, TaskItemFile, TaskTrigger } from './task';

const meta: Meta<typeof Task> = {
  title: 'AI/Task',
  component: Task,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Task>;

export const Default: Story = {
  render: () => (
    <Task>
      <TaskTrigger title="Locate billing CSV" />
      <TaskContent>
        <TaskItem>
          Downloaded file
          <TaskItemFile>billing-events.csv</TaskItemFile>
        </TaskItem>
        <TaskItem>Validated 124 rows</TaskItem>
        <TaskItem>Generated summary chart</TaskItem>
      </TaskContent>
    </Task>
  ),
};
