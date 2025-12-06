import { apiV1Path } from '@/lib/apiPaths';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';
type LogSink = 'console' | 'beacon' | 'none';

type LogPayload = {
  event: string;
  scope: string;
  level: LogLevel;
  message: string;
  timestamp: string;
  fields?: Record<string, unknown>;
};

const LEVEL_WEIGHT: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
};

const SENSITIVE_KEYS = [
  'authorization',
  'cookie',
  'password',
  'token',
  'refresh_token',
  'access_token',
  'secret',
  'key',
];

const envLevel = (process.env.NEXT_PUBLIC_LOG_LEVEL || 'info').toLowerCase() as LogLevel;
const envSink = (process.env.NEXT_PUBLIC_LOG_SINK || 'console').toLowerCase() as LogSink;
const activeLevel: LogLevel = LEVEL_WEIGHT[envLevel] ? envLevel : 'info';
const activeSink: LogSink = ['console', 'beacon', 'none'].includes(envSink) ? envSink : 'console';
const isBrowser = typeof window !== 'undefined';

const shouldLog = (level: LogLevel) => LEVEL_WEIGHT[level] >= LEVEL_WEIGHT[activeLevel];

function buildEvent(scope: string, message: string, fields?: Record<string, unknown>): string {
  if (fields && typeof fields.event === 'string' && fields.event.trim()) {
    return fields.event.trim().slice(0, 128);
  }
  const base = message ? `${scope}.${message}` : scope;
  return base.slice(0, 128);
}

function redact(value: unknown): unknown {
  if (value instanceof Error) {
    return {
      name: value.name,
      message: value.message,
      stack: value.stack,
      cause: value.cause ? redact(value.cause) : undefined,
    };
  }
  if (Array.isArray(value)) {
    return value.map(redact);
  }
  if (value && typeof value === 'object') {
    const result: Record<string, unknown> = {};
    for (const [key, v] of Object.entries(value)) {
      const normalized = key.toLowerCase();
      if (SENSITIVE_KEYS.some((needle) => normalized.includes(needle))) {
        result[key] = '[redacted]';
      } else {
        result[key] = redact(v);
      }
    }
    return result;
  }
  return value;
}

function emitConsole(payload: LogPayload) {
  const { level, message, scope, fields } = payload;
  const args: unknown[] = [`[${scope}]`, message];
  if (fields && Object.keys(fields).length > 0) {
    args.push(fields);
  }
  if (level === 'debug') {
    console.debug(...args);
  } else if (level === 'info') {
    console.info(...args);
  } else if (level === 'warn') {
    console.warn(...args);
  } else {
    console.error(...args);
  }
}

async function emitBeacon(payload: LogPayload) {
  if (!isBrowser) {
    emitConsole(payload);
    return;
  }
  const body = JSON.stringify(payload);

  if (navigator.sendBeacon) {
    const ok = navigator.sendBeacon(apiV1Path('/logs'), body);
    if (ok) return;
  }

  try {
    await fetch(apiV1Path('/logs'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body,
      keepalive: true,
    });
  } catch (error) {
    if (process.env.NODE_ENV !== 'production') {
      emitConsole({
        ...payload,
        level: 'debug',
        message: `${payload.message} (beacon fallback failed)`,
        fields: { error: String(error), ...(payload.fields || {}) },
      });
    }
  }
}

async function dispatch(payload: LogPayload) {
  if (activeSink === 'none') return;
  if (activeSink === 'beacon') {
    await emitBeacon(payload);
    return;
  }
  emitConsole(payload);
}

export function createLogger(scope: string) {
  const baseScope = scope || 'app';

  const log = async (level: LogLevel, message: string, fields?: Record<string, unknown>) => {
    if (!shouldLog(level)) return;
    const event = buildEvent(baseScope, message, fields);
    const payload: LogPayload = {
      event,
      scope: baseScope,
      level,
      message,
      timestamp: new Date().toISOString(),
      fields: fields ? (redact(fields) as Record<string, unknown>) : undefined,
    };
    await dispatch(payload);
  };

  return {
    debug: (message: string, fields?: Record<string, unknown>) => void log('debug', message, fields),
    info: (message: string, fields?: Record<string, unknown>) => void log('info', message, fields),
    warn: (message: string, fields?: Record<string, unknown>) => void log('warn', message, fields),
    error: (message: string, fields?: Record<string, unknown>) => void log('error', message, fields),
    child: (childScope: string) => createLogger(`${baseScope}:${childScope}`),
  };
}

export const logger = createLogger('app');
