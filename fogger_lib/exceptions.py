import logging
logger = logging.getLogger('fogger_lib')

class BaseFogAppException(BaseException):
    pass

class BadFogAppException(BaseFogAppException):
    pass
    def __init__(self, *args, **kwargs):
        logger.error('Misconfigured app. Please create the app again.')
        super(BadFogAppException, self).__init__(*args, **kwargs)

