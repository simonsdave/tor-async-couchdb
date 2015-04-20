#```tor_async_couchdb``` Basic Sample

Create
```bash
>curl -s -X POST http://127.0.0.1:2525/v1.0/fruits | python -m json.tool
```

Get individual 
```bash
>curl -s http://127.0.0.1:2525/v1.0/fruits/996e11bfd4224feabe32e157e74c7343 | python -m json.tool
```

Get all 
```bash
>curl -s http://127.0.0.1:2525/v1.0/fruits | python -m json.tool
```

Update
```bash
curl -s -X PUT http://127.0.0.1:2525/v1.0/fruits/996e11bfd4224feabe32e157e74c7343 | python -m json.tool
```

```bash
curl http://127.0.0.1:5984/tor_async_couchdb_basic_sample/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
```
