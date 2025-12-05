import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { LocationOptIn } from './LocationOptIn';
import type { LocationHint } from '@/lib/api/client/types.gen';

const meta: Meta<typeof LocationOptIn> = {
  title: 'UI/Forms/LocationOptIn',
  component: LocationOptIn,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

const DefaultExample = () => {
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
      />
    </div>
  );
};

export const Default: Story = {
  render: () => <DefaultExample />,
};

const EnabledExample = () => {
  const [shareLocation, setShareLocation] = useState(true);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
      />
    </div>
  );
};

export const Enabled: Story = {
  render: () => <EnabledExample />,
};

const WithValuesExample = () => {
  const [shareLocation, setShareLocation] = useState(true);
  const [location, setLocation] = useState<LocationHint>({
    city: 'San Francisco',
    region: 'California',
    country: 'United States',
    timezone: 'America/Los_Angeles',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
      />
    </div>
  );
};

export const WithValues: Story = {
  render: () => <WithValuesExample />,
};

const DisabledExample = () => {
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
        disabled
      />
    </div>
  );
};

export const Disabled: Story = {
  render: () => <DisabledExample />,
};

const WithoutOptionalBadgeExample = () => {
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
        showOptionalBadge={false}
      />
    </div>
  );
};

export const WithoutOptionalBadge: Story = {
  render: () => <WithoutOptionalBadgeExample />,
};

const CustomLabelsExample = () => {
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[600px]">
      <LocationOptIn
        shareLocation={shareLocation}
        onShareLocationChange={setShareLocation}
        location={location}
        onLocationChange={handleLocationChange}
        label="Enable location-based search results"
        tooltipText="We use your location to provide more relevant search results. Your exact location is never stored or shared."
      />
    </div>
  );
};

export const CustomLabels: Story = {
  render: () => <CustomLabelsExample />,
};

const InFormContextExample = () => {
  const [shareLocation, setShareLocation] = useState(false);
  const [location, setLocation] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const handleLocationChange = (field: keyof LocationHint, value: string) => {
    setLocation((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-full max-w-2xl space-y-4 p-6 border rounded-lg">
      <div>
        <h3 className="text-lg font-semibold mb-1">Search Preferences</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Configure how you want to receive search results
        </p>
      </div>

      <div className="space-y-4">
        <LocationOptIn
          shareLocation={shareLocation}
          onShareLocationChange={setShareLocation}
          location={location}
          onLocationChange={handleLocationChange}
        />

        <div className="flex gap-2 pt-4">
          <button className="px-4 py-2 rounded-md border bg-background hover:bg-accent">
            Cancel
          </button>
          <button className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90">
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
};

export const InFormContext: Story = {
  render: () => <InFormContextExample />,
};

const MultipleInstancesExample = () => {
  const [shareLocation1, setShareLocation1] = useState(false);
  const [location1, setLocation1] = useState<LocationHint>({
    city: '',
    region: '',
    country: '',
    timezone: '',
  });

  const [shareLocation2, setShareLocation2] = useState(true);
  const [location2, setLocation2] = useState<LocationHint>({
    city: 'New York',
    region: 'New York',
    country: 'United States',
    timezone: 'America/New_York',
  });

  const handleLocationChange1 = (field: keyof LocationHint, value: string) => {
    setLocation1((prev) => ({ ...prev, [field]: value }));
  };

  const handleLocationChange2 = (field: keyof LocationHint, value: string) => {
    setLocation2((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="w-[700px] space-y-6">
      <div className="p-4 border rounded-lg">
        <h4 className="font-semibold mb-3">Primary Location</h4>
        <LocationOptIn
          id="primary-location"
          shareLocation={shareLocation1}
          onShareLocationChange={setShareLocation1}
          location={location1}
          onLocationChange={handleLocationChange1}
          label="Use primary location for search"
        />
      </div>

      <div className="p-4 border rounded-lg">
        <h4 className="font-semibold mb-3">Alternative Location</h4>
        <LocationOptIn
          id="alt-location"
          shareLocation={shareLocation2}
          onShareLocationChange={setShareLocation2}
          location={location2}
          onLocationChange={handleLocationChange2}
          label="Use alternative location for search"
        />
      </div>
    </div>
  );
};

export const MultipleInstances: Story = {
  render: () => <MultipleInstancesExample />,
};
