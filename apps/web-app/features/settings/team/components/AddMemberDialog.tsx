'use client';

import { useEffect } from 'react';
import { z } from 'zod';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAuthForm } from '@/hooks/useAuthForm';
import { TEAM_ROLE_ORDER, type TeamRole } from '@/types/team';

const addMemberSchema = z.object({
  email: z.string().email('Enter a valid email.'),
  role: z.enum(TEAM_ROLE_ORDER as [TeamRole, ...TeamRole[]], {
    message: 'Select a role.',
  }),
});

interface AddMemberDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: { email: string; role: TeamRole }) => Promise<void>;
  isSubmitting?: boolean;
  roleOptions: Array<{ value: TeamRole; label: string; helper?: string }>;
}

export function AddMemberDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
  roleOptions,
}: AddMemberDialogProps) {
  const { form, onSubmit: handleSubmit } = useAuthForm({
    schema: addMemberSchema,
    initialValues: {
      email: '',
      role: roleOptions[0]?.value ?? 'member',
    },
    submitHandler: async (values) => {
      await onSubmit({
        email: values.email.trim(),
        role: values.role,
      });
      form.reset({ email: '', role: roleOptions[0]?.value ?? 'member' });
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({ email: '', role: roleOptions[0]?.value ?? 'member' });
    }
  }, [open, form, roleOptions]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add an existing user</DialogTitle>
          <DialogDescription>
            Add a user by email if they already have an account in another tenant.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>User email</FormLabel>
                  <FormControl>
                    <Input {...field} type="email" placeholder="member@acme.io" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {roleOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex flex-col">
                            <span>{option.label}</span>
                            {option.helper ? (
                              <span className="text-xs text-muted-foreground">
                                {option.helper}
                              </span>
                            ) : null}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="pt-2">
              <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Adding…' : 'Add member'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
