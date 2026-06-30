# Deploy to Render (free tier)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/dawit-Tegegnwork/application-support-runbook-lab)

## One-click deploy

1. Click **Deploy to Render** above.
2. Render reads [`render.yaml`](../render.yaml) and builds the Docker image.
3. After deploy, open `https://<your-service>.onrender.com/board` — triage board with INC-240601.
4. Runbooks live in the repo under `docs/runbooks/` (not served by the API).

## Quick test

```bash
curl https://<your-service>.onrender.com/health
curl https://<your-service>.onrender.com/api/tickets?ticket_number=INC-240601
```

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `sqlite:////tmp/support_tickets.db` | Ephemeral on free tier |

## Health check

Expected: `{"status":"ok","service":"application-support-runbook-lab"}`

**Synthetic incidents only.**
