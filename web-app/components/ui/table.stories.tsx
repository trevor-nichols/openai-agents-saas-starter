import type { Meta, StoryObj } from '@storybook/react';

import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './table';

const meta: Meta<typeof Table> = {
  title: 'UI/Data/Table',
  component: Table,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Table>;

export const Basic: Story = {
  render: () => (
    <Table>
      <TableCaption>Current active tenants</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Tenant</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Monthly Spend</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow>
          <TableCell>Acme Corp</TableCell>
          <TableCell>Active</TableCell>
          <TableCell className="text-right">$1,240</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Northwind</TableCell>
          <TableCell>Trial</TableCell>
          <TableCell className="text-right">$180</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>Globex</TableCell>
          <TableCell>Active</TableCell>
          <TableCell className="text-right">$3,420</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  ),
};
