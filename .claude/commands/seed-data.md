Reset and seed the Resonantia database with fresh demo data.

Steps:

1. Check current data counts:
```bash
docker exec resonantia-postgres-1 psql -U resonantia -d resonantia -c "
  SELECT 'experiments' as table_name, count(*) FROM experiments
  UNION ALL SELECT 'samples', count(*) FROM samples
  UNION ALL SELECT 'plate_maps', count(*) FROM plate_maps
  UNION ALL SELECT 'eln_entries', count(*) FROM eln_entries
  UNION ALL SELECT 'protocols', count(*) FROM protocols
  UNION ALL SELECT 'conversations', count(*) FROM conversations;
"
```

2. Optionally clear existing data (ask user first!):
```bash
docker exec resonantia-postgres-1 psql -U resonantia -d resonantia -c "
  TRUNCATE conversations, conversation_messages, eln_entries, eln_appendices, protocols, protocol_steps, experiments, plate_maps, samples, microscopy_images CASCADE;
"
```

3. Restart the backend to trigger seed on startup:
```bash
docker compose restart backend
```

4. Verify seeding worked:
```bash
sleep 5 && docker exec resonantia-postgres-1 psql -U resonantia -d resonantia -c "
  SELECT 'experiments' as table_name, count(*) FROM experiments
  UNION ALL SELECT 'samples', count(*) FROM samples
  UNION ALL SELECT 'plate_maps', count(*) FROM plate_maps;
"
```
