export interface ContactSubmission {
  name?: string | null;
  email: string;
  company?: string | null;
  topic?: string | null;
  message: string;
  /** Honeypot spam trap; should remain empty. */
  honeypot?: string | null;
}

