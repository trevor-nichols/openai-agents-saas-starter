import { Trash, Loader2 } from 'lucide-react';

import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

type Props = {
  onConfirm: () => void | Promise<void>;
  pending?: boolean;
  disabled?: boolean;
  tooltip?: string;
  stopPropagation?: boolean;
};

export function WorkflowRunDeleteButton({
  onConfirm,
  pending,
  disabled,
  tooltip = 'Delete run',
  stopPropagation = true,
}: Props) {
  return (
    <AlertDialog>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Delete workflow run"
                className="text-foreground/60 hover:text-destructive"
                disabled={disabled || pending}
                onClick={(e) => {
                  if (stopPropagation) {
                    e.stopPropagation();
                  }
                }}
              >
                {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash className="h-4 w-4" />}
              </Button>
            </AlertDialogTrigger>
          </TooltipTrigger>
          <TooltipContent side="top">{tooltip}</TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this workflow run?</AlertDialogTitle>
          <AlertDialogDescription>
            This removes the run and its steps from history. This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            onClick={() => onConfirm()}
            disabled={pending}
          >
            {pending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
