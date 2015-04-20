{
    "language": "javascript",
    "views": {
        "boo_by_boo_id": {
            "map": "function(doc) { if (doc.type.match(/^boo_v\\d+.\\d+/i)) { emit(doc.boo_id) } }"
        }
    }
}
