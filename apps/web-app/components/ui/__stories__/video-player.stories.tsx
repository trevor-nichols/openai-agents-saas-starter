import type { Meta, StoryObj } from '@storybook/react';

import {
  VideoPlayer,
  VideoPlayerContent,
  VideoPlayerControlBar,
  VideoPlayerMuteButton,
  VideoPlayerPlayButton,
  VideoPlayerSeekBackwardButton,
  VideoPlayerSeekForwardButton,
  VideoPlayerTimeDisplay,
  VideoPlayerTimeRange,
  VideoPlayerVolumeRange,
} from '../video-player';

const meta: Meta<typeof VideoPlayer> = {
  title: 'UI/Media/VideoPlayer',
  component: VideoPlayer,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof VideoPlayer>;

export const Default: Story = {
  render: () => (
    <VideoPlayer className="max-w-2xl">
      <VideoPlayerContent
        controls
        src="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
      />
      <VideoPlayerControlBar>
        <VideoPlayerPlayButton />
        <VideoPlayerSeekBackwardButton />
        <VideoPlayerSeekForwardButton />
        <VideoPlayerTimeRange />
        <VideoPlayerTimeDisplay />
        <VideoPlayerMuteButton />
        <VideoPlayerVolumeRange />
      </VideoPlayerControlBar>
    </VideoPlayer>
  ),
};
