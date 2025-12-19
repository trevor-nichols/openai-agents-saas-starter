import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { FileText, Moon, Sun } from 'lucide-react';

import { Button } from '../button';
import { Checkbox } from '../checkbox';
import { Dropzone, DropzoneContent, DropzoneEmptyState } from '../dropzone';
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '../form';
import { Input } from '../input';
import { Label } from '../label';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '../select';
import { Switch } from '../switch';
import { Textarea } from '../textarea';
import { Toggle } from '../toggle';
import { RadioGroup, RadioGroupItem } from '../radio-group';

const meta: Meta = {
  title: 'UI/Inputs/Form Controls',
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Inputs: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" placeholder="you@example.com" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="disabled">Disabled</Label>
        <Input id="disabled" placeholder="Cannot edit" disabled />
      </div>
      <div className="space-y-2">
        <Label htmlFor="bio">Bio</Label>
        <Textarea id="bio" placeholder="Tell us about your product..." />
      </div>
    </div>
  ),
};

const SelectAndRadiosComponent = () => {
  const [value, setValue] = useState('pro');
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <div className="space-y-2">
        <Label>Plan</Label>
        <Select value={value} onValueChange={setValue}>
          <SelectTrigger aria-label="Select plan">
            <SelectValue placeholder="Choose a plan" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Plans</SelectLabel>
              <SelectItem value="starter">Starter</SelectItem>
              <SelectItem value="pro">Pro</SelectItem>
              <SelectItem value="enterprise">Enterprise</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-3">
        <Label>Support SLA</Label>
        <RadioGroup defaultValue="standard">
          <label className="flex items-center gap-2 text-sm text-foreground/80">
            <RadioGroupItem value="standard" /> Standard (24h)
          </label>
          <label className="flex items-center gap-2 text-sm text-foreground/80">
            <RadioGroupItem value="priority" /> Priority (4h)
          </label>
        </RadioGroup>
      </div>
    </div>
  );
};

export const SelectAndRadios: Story = {
  render: () => <SelectAndRadiosComponent />,
};

export const Toggles: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-4">
      <div className="flex items-center gap-2">
        <Switch defaultChecked id="switch" />
        <Label htmlFor="switch" className="text-sm">
          Enable notifications
        </Label>
      </div>
      <Toggle aria-label="Bold" defaultPressed>
        <Sun className="h-4 w-4" />
        Light
      </Toggle>
      <Toggle aria-label="Italic">
        <Moon className="h-4 w-4" />
        Dark
      </Toggle>
    </div>
  ),
};

export const DropzoneField: Story = {
  render: () => {
    const file = new File(['Hello world'], 'example.txt', { type: 'text/plain' });
    return (
      <Dropzone src={[file]} accept={{ 'text/plain': ['.txt'] }} maxSize={1024 * 1024}>
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
    );
  },
};

type ProfileFormValues = {
  name: string;
  summary: string;
  terms: boolean;
};

const HookFormExampleComponent = () => {
  const form = useForm<ProfileFormValues>({
    defaultValues: {
      name: 'Ada Lovelace',
      summary: 'Building an AI agent platform.',
      terms: true,
    },
  });

  const onSubmit = form.handleSubmit((values) => {
    console.log('Submitted', values);
  });

    return (
      <Form {...form}>
        <form className="space-y-5 rounded-lg border border-white/10 p-6" onSubmit={onSubmit}>
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <Input placeholder="Your full name" {...field} />
                </FormControl>
                <FormDescription>We use this to personalize your workspace.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="summary"
            rules={{ minLength: { value: 10, message: 'Tell us a bit more (10+ chars).' } }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Project summary</FormLabel>
                <FormControl>
                  <Textarea placeholder="What are you building?" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="terms"
            render={({ field }) => (
              <FormItem className="flex flex-row items-center gap-3 rounded-lg border border-white/10 p-3">
                <FormControl>
                  <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                </FormControl>
                <div className="space-y-0.5 leading-none">
                  <FormLabel>Accept terms</FormLabel>
                  <FormDescription>You agree to our standard workspace terms.</FormDescription>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex items-center justify-end gap-2">
            <Button type="button" variant="outline" size="sm">
              <FileText className="h-4 w-4" />
              Preview
            </Button>
            <Button type="submit" size="sm">
              Save
            </Button>
          </div>
        </form>
      </Form>
    );
};

export const HookFormExample: Story = {
  render: () => <HookFormExampleComponent />,
};
