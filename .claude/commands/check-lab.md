Check the health of all Resonantia services. Run these checks and report status:

```bash
# 1. Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep resonantia

# 2. Backend health
curl -s http://localhost:8000/health | python3 -m json.tool

# 3. Database connectivity
docker exec resonantia-postgres-1 psql -U resonantia -d resonantia -c "SELECT count(*) as experiments FROM experiments; SELECT count(*) as samples FROM samples; SELECT count(*) as conversations FROM conversations;" 2>&1

# 4. Redis connectivity
docker exec resonantia-redis-1 redis-cli ping
docker exec resonantia-redis-1 redis-cli hlen resonantia:tools

# 5. Frontend status
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:3000

# 6. Temporal status
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8080

# 7. Backend logs (last 10 lines, errors only)
docker logs resonantia-backend-1 --tail 10 2>&1 | grep -i "error\|exception" || echo "No recent errors"
```

Report a summary table of service status (healthy/unhealthy/down) and flag any issues.
