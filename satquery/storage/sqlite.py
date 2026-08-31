from .base import StorageBackend

class SQLiteBackend(StorageBackend):
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.store = {}
        
    def save_analysis(self, analysis_id, data):
        self.store[analysis_id] = data
        
    def get_analysis(self, analysis_id):
        return self.store.get(analysis_id)
