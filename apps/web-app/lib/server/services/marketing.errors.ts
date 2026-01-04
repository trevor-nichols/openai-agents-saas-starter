import 'server-only';
export class MarketingServiceError extends Error {
  status: number;

  constructor(message: string, status = 500) {
    super(message);
    this.name = 'MarketingServiceError';
    this.status = status;
  }
}

