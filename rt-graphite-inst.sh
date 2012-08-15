# (The MIT License)
# Copyright (c) 2012 Sam Zaydel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

################################################################################
## Global Variables and Functions ##############################################
################################################################################



################################################################################
## Step 1a: Install latest updates #############################################
################################################################################

## These are required to install further Python components
##
apt-get update
apt-get install python-setuptools
apt-get install --no-install-recommends --assume-yes build-essential

## Pip is a package manager used for Python packages, and is needed to deploy Graphite
##
curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

pip install Fabric

## Now switching to fabric to install and configure all remaining bits

fab patch_os
fab install_blueprint
fab create_snapshot
fab install_deps
fab install_rest
fab configure
fab startup

