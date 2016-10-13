#
# BigBrotherBot(B3) (www.bigbrotherbot.net)
# Copyright (C) 2014 Courgette
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from tests import B3TestCase
from b3.plugins.ftpytail import FtpytailPlugin


class FtpytailPluginTestCase(B3TestCase):

    def test_load_plugin(self):
        p = FtpytailPlugin(self.console)
        p.onLoadConfig()

