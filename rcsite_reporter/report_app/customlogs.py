import logging

from report_app.report_logic.database_manipulator import note_log


db_default_formatter = logging.Formatter()

logging_levels = {
    0:  'NotSet',
    10: 'Debug',
    20: 'Info',
    30: 'Warning',
    40: 'Error',
    50: 'Fatal',
}


class CustomDBHandler(logging.Handler):
    def emit(self, record):

        trace = None

        if record.exc_info:
            trace = db_default_formatter.formatException(record.exc_info)

        msg = record.getMessage()

        note_log(
            logging_levels[int(record.levelno)],
            str(record.name),
            str(msg),
            str(trace)
        )
