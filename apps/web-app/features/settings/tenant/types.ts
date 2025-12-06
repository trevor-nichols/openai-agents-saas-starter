export interface PlanMetadataEntry {
  id: string;
  key: string;
  value: string;
}

export interface TenantFlagsState {
  [key: string]: boolean;
}
