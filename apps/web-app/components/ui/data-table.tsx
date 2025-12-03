'use client';

import { ArrowDown, ArrowUp, ArrowUpDown } from 'lucide-react';
import { type ReactNode, useState } from 'react';
import type { Cell, ColumnDef, Header, HeaderGroup, Row } from '@tanstack/react-table';
import {
  SortingState,
  Table as ReactTable,
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { SkeletonPanel } from '@/components/ui/states/SkeletonPanel';
import { EmptyState } from '@/components/ui/states/EmptyState';
import { ErrorState } from '@/components/ui/states/ErrorState';
import { cn } from '@/lib/utils';

interface DataTableProps<TData extends object> {
  columns: ColumnDef<TData, unknown>[];
  data: TData[];
  className?: string;
  isLoading?: boolean;
  isError?: boolean;
  error?: string;
  emptyState?: ReactNode;
  onRowClick?: (row: Row<TData>) => void;
  enableSorting?: boolean;
  enablePagination?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  skeletonLines?: number;
  rowClassName?: string;
  onRowMouseEnter?: (row: Row<TData>) => void;
  onRowFocus?: (row: Row<TData>) => void;
}

export function DataTable<TData extends object>({
  columns,
  data,
  className,
  isLoading = false,
  isError = false,
  error,
  emptyState,
  onRowClick,
  enableSorting = true,
  enablePagination = false,
  pageSize = 10,
  pageSizeOptions = [10, 20, 50],
  skeletonLines = 6,
  rowClassName,
  onRowMouseEnter,
  onRowFocus,
}: DataTableProps<TData>) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize,
  });

  // TanStack Table returns mutable helpers; safe to opt out of React Compiler memoization here.
  const table = useReactTable<TData>({
    data,
    columns,
    state: {
      sorting,
      pagination,
    },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    pageCount: Math.ceil(data.length / pagination.pageSize),
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: enableSorting ? getSortedRowModel() : undefined,
    getPaginationRowModel: enablePagination ? getPaginationRowModel() : undefined,
    enableSorting,
  });

  let content: React.ReactNode;

  if (isLoading) {
    content = <SkeletonPanel lines={skeletonLines} className="rounded-2xl" />;
  } else if (isError) {
    content = (
      <ErrorState
        title="Unable to load rows"
        message={error ?? 'An error occurred while fetching table data.'}
      />
    );
  } else if (data.length === 0) {
    content = (
      <div>{emptyState ?? <EmptyState title="No data yet" description="Nothing to show right now." />}</div>
    );
  } else {
    const rows = table.getRowModel().rows;
    content = (
      <ScrollArea className="max-h-[520px] overflow-hidden rounded-2xl border shadow-sm">
        <Table className="min-w-full text-sm">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup: HeaderGroup<TData>) => (
              <TableRow key={headerGroup.id} className="hover:bg-transparent">
                {headerGroup.headers.map((header: Header<TData, unknown>) => (
                  <TableHead key={header.id} className="px-4 py-3 h-12">
                    {header.isPlaceholder ? null : (
                      <div
                        className={cn(
                          'flex items-center justify-between gap-2',
                          enableSorting ? 'cursor-pointer select-none' : '',
                        )}
                        onClick={enableSorting ? header.column.getToggleSortingHandler() : undefined}
                      >
                        <span>{flexRender(header.column.columnDef.header, header.getContext())}</span>
                        {enableSorting && (
                          <span className="flex items-center gap-1">
                            {header.column.getIsSorted() === 'asc' ? (
                              <ArrowUp className="h-3 w-3" />
                            ) : header.column.getIsSorted() === 'desc' ? (
                              <ArrowDown className="h-3 w-3" />
                            ) : (
                              <ArrowUpDown className="h-3 w-3 opacity-50" />
                            )}
                          </span>
                        )}
                      </div>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {rows.map((row: Row<TData>) => (
              <TableRow
                key={row.id}
                className={cn(
                  'border-t border-border/40 transition-colors hover:bg-muted/30 focus-visible:bg-muted/30',
                  onRowClick ? 'cursor-pointer' : '',
                  rowClassName,
                )}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                onMouseEnter={onRowMouseEnter ? () => onRowMouseEnter(row) : undefined}
                onFocus={onRowFocus ? () => onRowFocus(row) : undefined}
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.preventDefault();
                          onRowClick(row);
                        }
                      }
                    : undefined
                }
              >
                {row.getVisibleCells().map((cell: Cell<TData, unknown>) => (
                  <TableCell key={cell.id} className="px-4 py-3 text-foreground/80 whitespace-nowrap align-middle">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </ScrollArea>
    );
  }

  return (
    <div className={cn('flex flex-col gap-4', className)}>
      {content}
      {enablePagination && !isLoading && !isError && data.length > 0 ? (
        <DataTablePagination
          table={table}
          pageSizeOptions={pageSizeOptions}
        />
      ) : null}
    </div>
  );
}

interface DataTablePaginationProps<TData extends object> {
  table: ReactTable<TData>;
  pageSizeOptions?: number[];
}

function DataTablePagination<TData extends object>({
  table,
  pageSizeOptions = [10, 20, 50],
}: DataTablePaginationProps<TData>) {
  const { pagination } = table.getState();
  const rows = table.getRowModel().rows;
  const totalRows = table.getCoreRowModel().rows.length;
  const start = totalRows === 0 ? 0 : pagination.pageIndex * pagination.pageSize + 1;
  const end = Math.min(start + rows.length - 1, totalRows);

  const canPrevious = table.getCanPreviousPage();
  const canNext = table.getCanNextPage();

  return (
    <div className="flex flex-wrap items-center justify-between gap-4 px-4 py-3 text-xs text-foreground/70">
      <p>
        Showing {start}-{end} of {totalRows}
      </p>
      <div className="flex items-center gap-2">
        <span className="text-[11px]">Rows per page</span>
        <Select value={String(pagination.pageSize)} onValueChange={(value) => table.setPageSize(Number(value))}>
          <SelectTrigger className="w-24">
            <SelectValue placeholder={String(pagination.pageSize)} />
          </SelectTrigger>
          <SelectContent position="popper">
            <SelectGroup>
              {pageSizeOptions.map((size) => (
                <SelectItem key={size} value={String(size)}>
                  {size}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={() => table.previousPage()} disabled={!canPrevious}>
            Previous
          </Button>
          <Button variant="secondary" size="sm" onClick={() => table.nextPage()} disabled={!canNext}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}

export { DataTablePagination };
