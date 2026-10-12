import {defineRailway,github,preserve,project,service} from 'railway/iac';

// Reuse the backend service and deploy its production branch natively.
export default defineRailway(()=>project('CareerGrowth',{
  resources:[service('backend',{
    source:github('Jehad-Adel/CareerGrowth',{branch:'main',rootDirectory:'backend'}),
    rootDirectory:'backend',
    build:{builder:'DOCKERFILE',dockerfilePath:'backend/Dockerfile'},
    healthcheck:'/health',
    healthcheckTimeout:60,
    preDeploy:'alembic upgrade head',
    deploy:{restartPolicyType:'ON_FAILURE',restartPolicyMaxRetries:3},
    // Keep Docker CMD as the start path: it expands PORT and execs uvicorn.
    env:{ENVIRONMENT:'production',DEBUG:'false',TRUSTED_PROXY_COUNT:'1',
      DATABASE_URL:preserve(),DIRECT_DATABASE_URL:preserve(),SUPABASE_URL:preserve(),
      GOOGLE_API_KEY:preserve(),CORS_ORIGINS:preserve(),SENTRY_DSN:preserve(),
      GEMINI_MODEL:preserve(),TEMPERATURE:preserve(),MAX_OUTPUT_TOKENS:preserve(),PORT:preserve(),
    },
  })],
}));
