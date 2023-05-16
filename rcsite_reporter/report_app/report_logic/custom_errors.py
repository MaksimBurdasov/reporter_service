class FileFormatError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None


class BitBucketWorkError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None


class DBWorkError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None


class PutInMountFolderError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None


class MountFolderError(Exception):
    def __init__(self, *args):
        self.message = args[0] if args else None