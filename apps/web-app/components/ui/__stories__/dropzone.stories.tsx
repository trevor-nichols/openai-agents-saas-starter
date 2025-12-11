import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { Dropzone, DropzoneContent, DropzoneEmptyState } from '../dropzone';

const meta: Meta<typeof Dropzone> = {
  title: 'UI/Inputs/Dropzone',
  component: Dropzone,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const DefaultExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <Dropzone
      src={files}
      onDrop={(acceptedFiles) => {
        setFiles(acceptedFiles);
      }}
      className="w-[400px]"
    >
      <DropzoneEmptyState />
      <DropzoneContent />
    </Dropzone>
  );
};

export const Default: Story = {
  render: () => <DefaultExample />,
};

const SingleFileExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Upload Profile Picture</label>
      <Dropzone
        src={files}
        onDrop={(acceptedFiles) => {
          setFiles(acceptedFiles);
        }}
        maxFiles={1}
        accept={{ 'image/*': [] }}
        className="w-[400px]"
      >
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
      <p className="text-xs text-muted-foreground">
        Upload a single image file
      </p>
    </div>
  );
};

export const SingleFile: Story = {
  render: () => <SingleFileExample />,
};

const MultipleFilesExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Upload Documents</label>
      <Dropzone
        src={files}
        onDrop={(acceptedFiles) => {
          setFiles(acceptedFiles);
        }}
        maxFiles={5}
        className="w-[400px]"
      >
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
      <p className="text-xs text-muted-foreground">
        Upload up to 5 files
      </p>
    </div>
  );
};

export const MultipleFiles: Story = {
  render: () => <MultipleFilesExample />,
};

const WithFileTypeRestrictionsExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Upload PDF Documents</label>
      <Dropzone
        src={files}
        onDrop={(acceptedFiles) => {
          setFiles(acceptedFiles);
        }}
        accept={{ 'application/pdf': ['.pdf'] }}
        maxFiles={3}
        className="w-[400px]"
      >
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
    </div>
  );
};

export const WithFileTypeRestrictions: Story = {
  render: () => <WithFileTypeRestrictionsExample />,
};

const WithSizeLimitExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <div className="grid gap-2">
      <label className="text-sm font-medium">Upload Image</label>
      <Dropzone
        src={files}
        onDrop={(acceptedFiles) => {
          setFiles(acceptedFiles);
        }}
        accept={{ 'image/*': [] }}
        maxSize={5 * 1024 * 1024} // 5MB
        maxFiles={1}
        onError={(error) => {
          console.error('Upload error:', error);
        }}
        className="w-[400px]"
      >
        <DropzoneEmptyState />
        <DropzoneContent />
      </Dropzone>
    </div>
  );
};

export const WithSizeLimit: Story = {
  render: () => <WithSizeLimitExample />,
};

const ImagesOnlyExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <Dropzone
      src={files}
      onDrop={(acceptedFiles) => {
        setFiles(acceptedFiles);
      }}
      accept={{
        'image/png': ['.png'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp'],
      }}
      maxFiles={4}
      className="w-[400px]"
    >
      <DropzoneEmptyState />
      <DropzoneContent />
    </Dropzone>
  );
};

export const ImagesOnly: Story = {
  render: () => <ImagesOnlyExample />,
};

const DisabledExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <Dropzone
      src={files}
      onDrop={(acceptedFiles) => {
        setFiles(acceptedFiles);
      }}
      disabled
      className="w-[400px]"
    >
      <DropzoneEmptyState />
      <DropzoneContent />
    </Dropzone>
  );
};

export const Disabled: Story = {
  render: () => <DisabledExample />,
};

const CustomContentExample = () => {
  const [files, setFiles] = useState<File[]>();

  return (
    <Dropzone
      src={files}
      onDrop={(acceptedFiles) => {
        setFiles(acceptedFiles);
      }}
      className="w-[400px]"
    >
      <DropzoneEmptyState>
        <div className="text-center">
          <p className="font-semibold">Drop your files here</p>
          <p className="text-sm text-muted-foreground mt-1">
            or click to browse
          </p>
        </div>
      </DropzoneEmptyState>
      <DropzoneContent>
        {files && (
          <div className="text-center">
            <p className="font-semibold">
              {files.length} file{files.length > 1 ? 's' : ''} selected
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              Click to replace
            </p>
          </div>
        )}
      </DropzoneContent>
    </Dropzone>
  );
};

export const CustomContent: Story = {
  render: () => <CustomContentExample />,
};
