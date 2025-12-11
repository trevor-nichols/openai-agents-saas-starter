import type { Meta, StoryObj } from '@storybook/react';
import type { ColumnDef } from '@tanstack/react-table';

import { DataTable } from '../data-table';

type Workspace = {
  name: string;
  owner: string;
  region: string;
  usage: number;
};

const rows: Workspace[] = [
  { name: 'Support', owner: 'Ada Lovelace', region: 'us-east-1', usage: 142000 },
  { name: 'Research', owner: 'Alan Turing', region: 'eu-west-1', usage: 68000 },
  { name: 'Analytics', owner: 'Grace Hopper', region: 'us-west-2', usage: 92000 },
  { name: 'Sandbox', owner: 'Edsger Dijkstra', region: 'ap-southeast-1', usage: 12000 },
];

const columns: ColumnDef<Workspace>[] = [
  {
    header: 'Workspace',
    accessorKey: 'name',
    cell: ({ getValue }) => <span className="font-medium">{getValue<string>()}</span>,
  },
  {
    header: 'Owner',
    accessorKey: 'owner',
  },
  {
    header: 'Region',
    accessorKey: 'region',
  },
  {
    header: 'Usage',
    accessorKey: 'usage',
    cell: ({ getValue }) => `${getValue<number>().toLocaleString()} tokens`,
  },
];

const meta: Meta<typeof DataTable<Workspace>> = {
  title: 'UI/Data/DataTable',
  component: DataTable,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => {
    return (
      <DataTable
        columns={columns}
        data={rows}
        enablePagination
        pageSize={2}
        className="max-w-3xl"
      />
    );
  },
};

export const Loading: Story = {
  args: {
    columns,
    data: [],
    isLoading: true,
    className: 'max-w-3xl',
  },
};

export const Empty: Story = {
  args: {
    columns,
    data: [],
    className: 'max-w-3xl',
  },
};
