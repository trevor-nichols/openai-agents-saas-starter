import { shellActivityEvents } from '../../components/shell/__stories__/fixtures';

const badgeCount = 2;

export const fetchActivityPage = async () => ({
  items: shellActivityEvents,
  next_cursor: null,
  unread_count: badgeCount,
});

export const markActivityRead = async () => Math.max(badgeCount - 1, 0);

export const dismissActivity = async () => badgeCount;

export const markAllActivityRead = async () => 0;
