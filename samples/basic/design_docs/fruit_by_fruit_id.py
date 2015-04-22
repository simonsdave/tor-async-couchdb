{
    "language": "javascript",
    "views": {
        "fruit_by_fruit_id": {
            "map": "function(doc) { if (doc.type.match(/^fruit_v\\d+.\\d+/i)) { emit(doc.fruit_id) } }"
        }
    }
}
