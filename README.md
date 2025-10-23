# BitTorrent Extractor

Largly dockerized now -- see the example compose, and then run:

```
docker compose -f btex-compose.yml up -d
```

Do be aware that the application expects torrents to show up (inside the container) in `/srv/finished`.
