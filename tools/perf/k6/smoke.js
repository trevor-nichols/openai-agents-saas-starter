import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.PERF_BASE_URL || 'http://127.0.0.1:8000';
const TENANT_SLUG = __ENV.PERF_TENANT_SLUG || 'smoke';
const TENANT_NAME = __ENV.PERF_TENANT_NAME || 'Smoke Test Tenant';
const ADMIN_EMAIL = __ENV.PERF_ADMIN_EMAIL || 'smoke-admin@example.com';
const ADMIN_PASSWORD = __ENV.PERF_ADMIN_PASSWORD || 'SmokeAdmin!234';
const ACCESS_TOKEN = __ENV.PERF_ACCESS_TOKEN;
const TENANT_ID = __ENV.PERF_TENANT_ID;

const CHAT_MESSAGE = __ENV.PERF_CHAT_MESSAGE || 'Hello from perf smoke.';
const WORKFLOW_MESSAGE = __ENV.PERF_WORKFLOW_MESSAGE || 'Summarize quickly.';

const VUS = Number(__ENV.PERF_VUS || 1);
const DURATION = __ENV.PERF_DURATION || '30s';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: VUS,
      duration: DURATION,
      gracefulStop: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1500', 'p(99)<3000'],
  },
};

function jsonHeaders(extra) {
  return {
    headers: {
      'Content-Type': 'application/json',
      ...(extra || {}),
    },
  };
}

function ensureStatus(res, expected, label) {
  const ok = check(res, {
    [label]: (r) => r.status === expected,
  });
  if (!ok) {
    throw new Error(`${label} failed with status ${res.status}`);
  }
}

function applyFixtures(baseUrl) {
  const payload = {
    tenants: [
      {
        slug: TENANT_SLUG,
        name: TENANT_NAME,
        users: [
          {
            email: ADMIN_EMAIL,
            password: ADMIN_PASSWORD,
            display_name: 'Perf Admin',
            role: 'owner',
            verify_email: true,
          },
        ],
      },
    ],
  };

  const res = http.post(`${baseUrl}/api/v1/test-fixtures/apply`, JSON.stringify(payload), jsonHeaders());
  if (res.status === 404) {
    throw new Error(
      'Test fixtures endpoint is disabled. Set USE_TEST_FIXTURES=true or provide PERF_ACCESS_TOKEN/PERF_TENANT_ID.'
    );
  }
  ensureStatus(res, 201, 'apply fixtures (201)');

  const body = res.json();
  const tenant = body?.tenants?.[TENANT_SLUG];
  if (!tenant?.tenant_id) {
    throw new Error('Fixture response missing tenant_id.');
  }
  return tenant.tenant_id;
}

function login(baseUrl, tenantId) {
  const payload = {
    email: ADMIN_EMAIL,
    password: ADMIN_PASSWORD,
    tenant_id: tenantId,
  };
  const res = http.post(`${baseUrl}/api/v1/auth/token`, JSON.stringify(payload), jsonHeaders());
  ensureStatus(res, 200, 'login (200)');
  const body = res.json();
  if (!body?.access_token) {
    throw new Error('Login response missing access_token.');
  }
  return {
    accessToken: body.access_token,
    tenantId: body.tenant_id || tenantId,
  };
}

export function setup() {
  if (ACCESS_TOKEN && TENANT_ID) {
    return {
      baseUrl: BASE_URL,
      accessToken: ACCESS_TOKEN,
      tenantId: TENANT_ID,
    };
  }

  const tenantId = applyFixtures(BASE_URL);
  const auth = login(BASE_URL, tenantId);

  return {
    baseUrl: BASE_URL,
    accessToken: auth.accessToken,
    tenantId: auth.tenantId,
  };
}

export default function (data) {
  const headers = {
    Authorization: `Bearer ${data.accessToken}`,
    'X-Tenant-Id': data.tenantId,
    'X-Tenant-Role': 'owner',
    'Content-Type': 'application/json',
  };

  const health = http.get(`${data.baseUrl}/health`);
  ensureStatus(health, 200, 'health (200)');

  const chat = http.post(
    `${data.baseUrl}/api/v1/chat`,
    JSON.stringify({ message: CHAT_MESSAGE, agent_type: 'triage' }),
    { headers }
  );
  ensureStatus(chat, 200, 'chat (200)');

  const workflow = http.post(
    `${data.baseUrl}/api/v1/workflows/analysis_code/run`,
    JSON.stringify({ message: WORKFLOW_MESSAGE }),
    { headers }
  );
  ensureStatus(workflow, 200, 'workflow (200)');

  sleep(1);
}
