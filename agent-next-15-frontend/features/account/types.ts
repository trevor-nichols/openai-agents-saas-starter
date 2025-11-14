import { ACCOUNT_TABS } from './constants';

export type AccountTabKey = (typeof ACCOUNT_TABS)[number]['key'];

export interface AccountOverviewProps {
  initialTab?: string;
}
