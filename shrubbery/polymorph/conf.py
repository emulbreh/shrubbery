from shrubbery.conf import Settings, Setting

class settings(Settings):
    OBJECT_IDENTITY_DB_TABLE = Setting(default=None)
    OBJECT_IDENTITY_DB_COLUMN = Setting(default='identity_id')