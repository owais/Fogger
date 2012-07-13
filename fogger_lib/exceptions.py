### BEGIN LICENSE
# Copyright (C) 2012 Owais Lone <hello@owaislone.org>
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE
import logging
logger = logging.getLogger('fogger_lib')

class BaseFogAppException(BaseException):
    pass

class BadFogAppException(BaseFogAppException):
    pass
    def __init__(self, *args, **kwargs):
        logger.error('Misconfigured app. Please create the app again.')
        super(BadFogAppException, self).__init__(*args, **kwargs)

