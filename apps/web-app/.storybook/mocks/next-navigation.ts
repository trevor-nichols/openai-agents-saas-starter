type MockRouter = {
  push: (href: string) => void;
  replace?: (href: string) => void;
  refresh: () => void;
  prefetch?: (href: string) => Promise<void>;
};

let currentPathname = '/';
let currentRouter: MockRouter = {
  push: () => {},
  refresh: () => {},
  replace: () => {},
  prefetch: async () => {},
};

export const setMockPathname = (pathname: string) => {
  currentPathname = pathname;
};

export const setMockRouter = (router: Partial<MockRouter>) => {
  currentRouter = { ...currentRouter, ...router };
};

export function useRouter(): MockRouter {
  return currentRouter;
}

export function usePathname(): string {
  return currentPathname;
}

export function redirect(_href: string): never {
  throw new Error('next/navigation redirect is not supported in Storybook.');
}

export function useSearchParams(): URLSearchParams {
  return new URLSearchParams(globalThis.location?.search ?? '');
}

export function useParams<T extends Record<string, string | string[]>>(): T {
  return {} as T;
}

export function useSelectedLayoutSegments(): string[] {
  return [];
}
