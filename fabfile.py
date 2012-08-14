__author__ = 'szaydel'

#import re
from fabric.api import abort as fab_abort
from fabric.api import hosts
from fabric.api import lcd as fab_lcd
from fabric.api import local as fab_local
from fabric.api import run as fab_run
from fabric.api import prompt as fab_prompt
from fabric.operations import put as fab_put


from fabric.api import settings, env
from fabric.context_managers import hide
from fabric.context_managers import show
from fabric.tasks import execute as fab_execute
from fabric.api import task
from fabric.utils import puts as fab_puts
from fabric.tasks import Task
from fabric.contrib.console import confirm as fab_confirm


## Non-fabric related imports
from os import listdir as os_listdir
from os import mkdir as os_mkdir
from os import symlink as os_symlink
from os import path as os_path
from os import walk as os_walk
from shutil import copyfile
from string import Template
from sys import exit as sys_exit
from time import localtime
import re
import glob


apache_base_templ = '''<IfModule !wsgi_module.c>
    LoadModule wsgi_module modules/mod_wsgi.so
</IfModule>
WSGISocketPrefix $wsgi_sockd
<VirtualHost *:$port>
        ServerName graphite
        DocumentRoot "/opt/graphite/webapp"
        ErrorLog /opt/graphite/storage/log/webapp/error.log
        CustomLog /opt/graphite/storage/log/webapp/access.log common
        WSGIDaemonProcess graphite processes=5 threads=5 display-name='%{GROUP}' inactivity-timeout=120
        WSGIProcessGroup graphite
        WSGIApplicationGroup %{GLOBAL}
        WSGIImportScript /opt/graphite/conf/graphite.wsgi process-group=graphite application-group=%{GLOBAL}
        WSGIScriptAlias / /opt/graphite/conf/graphite.wsgi
        Alias /content/ /opt/graphite/webapp/content/
        <Location "/content/">
                SetHandler None
        </Location>
        Alias /media/ "@DJANGO_ROOT@/contrib/admin/media/"
        <Location "/media/">
                SetHandler None
        </Location>
        <Directory /opt/graphite/conf/>
                Order deny,allow
                Allow from all
        </Directory>
</VirtualHost>
'''

stor_base_templ = '''
[arc_statistics_5sec_for_2weeks_1min_for_20days_10min_for_90days]
pattern = ^brickstor\.*.*\.arcstats\.*.*$
retentions = 5s:14d,1m:20d,10m:90d
'''

@task
def patch_os(ag='apt-get'):
    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):
        apt_upd = fab_local('apt-get update',capture=True)

        if apt_upd.failed:
            fab_puts("{0}".format('Aptitude failed to complete updating.'), show_prefix=False)

        if apt_upd.succeeded:
            ## If we successfully updated, let's actually upgrade packages
            apt_upgr = fab_local("{0} {1}".format(ag,'dist-upgrade --assume-yes'),
                                 capture=True)

@task
def install_blueprint(ag='apt-get'):
    devs_repo = '/etc/apt/sources.list.d/devstructure.list'
    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):
        x = open('/etc/lsb-release').readlines()

        for line in x:
            if not line.find('DISTRIB_CODENAME') == -1:

                vers = line.split('=')[1].strip('\n')
                open(devs_repo,'wt')\
                .write("deb http://packages.devstructure.com {0} main".format(vers))

        inst_bluep = fab_local("wget -O {0} {1}".format(
         '/etc/apt/trusted.gpg.d/devstructure.gpg',
         'http://packages.devstructure.com/keyring.gpg'
        ))

        apt_upd = fab_local('apt-get update',capture=True)
        if apt_upd.succeeded:
            fab_local("{0} {1}".format(ag,'install --no-install-recommends --assume-yes blueprint'))

@task
def create_snapshot():
    message = '\"Snapshot before graphite and its dependencies\"'
    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):

        x = localtime()
        ## Month needs to always be 2 digits XX, bug.
        ts = "{0}{1}{2}".format(x.tm_year,x.tm_mon,x.tm_mday)

        bpcreate = fab_local("blueprint create --sh --message {0} bluep-{1}-001".format(message,ts),capture=True)

        if bpcreate.succeeded:
            fab_puts("Blueprint created checkpoint.", show_prefix=False)


@task
def install_deps(ag='apt-get --dry-run'):
    reqs = ['apache2', 'libapache2-mod-wsgi',
    'libapache2-mod-python', 'memcached', 'python-dev', 'python-cairo-dev',
    'python-django', 'python-ldap', 'python-memcache', 'python-pysqlite2',
    'sqlite3', 'erlang-os-mon', 'erlang-snmp', 'rabbitmq-server']

    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):

        fab_local("{0} install --no-install-recommends {1}".format(ag," ".join(reqs)))
        fab_local('pip install django-tagging')

        if inst_reqs.succeeded:
            fab_puts("Installed Prerequisites for Graphite.", show_prefix=False)


@task
def install_rest(pip_cmd='pip install'):

    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):

        fab_local("{0} carbon --install-option=\"--prefix={1}\" \
                  \"--install-option=--install-lib={1}/lib\"".format(pip_cmd,'/opt/graphite'))

        fab_local("{0} graphite-web --install-option=\"--prefix={1}\" \
                  \"--install-option=--install-lib={1}/webapp\"".format(pip_cmd,'/opt/graphite'))

        fab_local("{0} {1}".format(pip_cmd,'whisper'))


@task
def configure():
    graph_conf_path='/opt/graphite/conf'
    graph_stor_path = '/opt/graphite/storage'
    apache_avail = '/etc/apache2/sites-available'
    apache_enab = '/etc/apache2/sites-enabled'
    apache_src_conf = '/root/default-graphite'
    apache_dst_conf = "{0}/{1}".format(apache_avail,'default-graphite')
    apache_enab_conf = "{0}/{1}".format(apache_enab,'default-graphite')
    stor_sch_conf = "{0}/{1}".format(graph_conf_path,'storage-schemas.conf')

    with settings(
        show('running',
             'stdout',
             'stderr'),
        warn_only=True, always_use_pty='false'):

        for file in ['carbon.conf','storage-schemas.conf','graphite.wsgi']:

            src = "{0}/{1}.example".format(graph_conf_path,file)
            dst = "{0}/{1}".format(graph_conf_path,file)
            ## Copy from example, template to real file
            copyfile(src,dst)

        ## Generate default-graphite apache config file, based on
        ## template at top of this file.
        make_apache_conf = Template(apache_base_templ)

        ## Write template into the new config file
        ## /etc/apache2/sites-available/default-graphite

        open(apache_dst_conf,'wt').write(
            make_apache_conf.substitute(port=80,wsgi_sockd='/etc/httpd/wsgi/')
        )

        open(stor_sch_conf,'at').write(stor_base_templ)

        ## Create necessary directories for Apache
        for dir in ['/etc/httpd','/etc/httpd/wsgi']:
            try:
                os_mkdir(dir,0755)
            except OSError as e:
                print "Warning: {0} {1}".format(e.filename,e.args)

        try:
            os_symlink(apache_dst_conf, apache_enab_conf)

        except OSError as e:
            print "Warning: {0} {1}".format(e.filename,e.args)

        with fab_lcd('/opt/graphite/webapp/graphite/'):
            fab_local('python manage.py syncdb')

        ## This should really use python os module, will fix later.
        fab_local("chown -R {0} {1}".format('www-data:www-data',graph_stor_path))

        ## Copy local_settings.py.example config into real config file
        src = '/opt/graphite/webapp/graphite/local_settings.py.example'
        dst = '/opt/graphite/webapp/graphite/local_settings.py'
        copyfile(src,dst)

        ## Reload Apache config after all the changes
        fab_local("/etc/init.d/apache2 reload")