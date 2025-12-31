import { z } from 'zod';

export const tenantNameSchema = z
  .string()
  .trim()
  .min(2, 'Provide a tenant name.')
  .max(80, 'Keep names under 80 characters.');

export const tenantSlugSchema = z
  .string()
  .trim()
  .min(2, 'Slug must be at least 2 characters.')
  .max(64, 'Slug must be 64 characters or less.');

export const optionalSlugSchema = z.preprocess(
  (value) => {
    if (typeof value === 'string') {
      const trimmed = value.trim();
      return trimmed.length > 0 ? trimmed : undefined;
    }
    return value;
  },
  tenantSlugSchema.optional(),
);

export function buildTenantEditSchema(currentSlug?: string | null) {
  const slugField = z
    .union([z.literal(''), tenantSlugSchema])
    .refine(
      (value) => !(currentSlug && value === ''),
      { message: 'Slug cannot be cleared once set.' },
    );
  return z.object({
    name: tenantNameSchema,
    slug: slugField,
  });
}
