import type { Decorator, Preview } from '@storybook/react';
import React from 'react';
import { StoryProviders } from './StoryProviders';

const withProviders: Decorator = (Story, context) => {
  return React.createElement(
    StoryProviders,
    { theme: context.globals.theme },
    React.createElement(Story)
  );
};

const preview: Preview = {
  decorators: [withProviders],
  parameters: {
    layout: 'padded',
    actions: { argTypesRegex: '^on[A-Z].*' },
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
      expanded: true,
    },
    backgrounds: {
      default: 'Dark',
      values: [
        { name: 'Dark', value: 'hsl(220, 16%, 7%)' },
        { name: 'Light', value: 'hsl(220, 12%, 96%)' },
        { name: 'Accent', value: 'hsl(211, 100%, 72%)' },
      ],
    },
    viewport: {
      viewports: {
        mobile: {
          name: 'Mobile (430px)',
          styles: { width: '430px', height: '800px' },
        },
        tablet: {
          name: 'Tablet (834px)',
          styles: { width: '834px', height: '1112px' },
        },
        desktop: {
          name: 'Desktop (1280px)',
          styles: { width: '1280px', height: '800px' },
        },
      },
    },
    options: {
      storySort: {
        method: 'alphabetical',
      },
    },
    nextjs: {
      navigation: {
        pathname: '/',
        push: () => {},
        replace: () => {},
        refresh: () => {},
        forward: () => {},
        back: () => {},
      },
    },
  },
  globalTypes: {
    theme: {
      name: 'Theme',
      description: 'Global theme for components',
      defaultValue: 'light',
      toolbar: {
        icon: 'circlehollow',
        items: [
          { value: 'light', title: 'Light' },
          { value: 'dark', title: 'Dark' },
          { value: 'system', title: 'System' },
        ],
        dynamicTitle: true,
      },
    },
  },
};

export default preview;
