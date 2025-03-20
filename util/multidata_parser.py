class Part:
    def __init__(self, headers, name, content):
        self.headers = headers
        self.name = name
        self.content = content

class MultiDataParser:
    def __init__(self, boundary, parts):
        self.boundary = boundary
        self.parts = parts
