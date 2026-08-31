class ModelLifecycle:
    STATES = ['UNINITIALIZED', 'LOADING', 'READY', 'FAILED', 'UNLOADING', 'UNAVAILABLE']
    def __init__(self):
        self.state = 'UNINITIALIZED'
    def load(self):
        self.state = 'READY'
    def unload(self):
        self.state = 'UNINITIALIZED'
