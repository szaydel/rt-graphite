### Install latest updates first

sudo apt-get update
sudo apt-get dist-upgrade -y

## reboot <= likely necessary

sudo apt-get install python-setuptools
sudo apt-get install --no-install-recommends -y build-essential

curl https://raw.github.com/pypa/pip/master/contrib/get-pip.py | sudo python
sudo pip install Fabric

### Install blueprint to snapshot system's configuration
echo "deb http://packages.devstructure.com $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/devstructure.list
sudo wget -O /etc/apt/trusted.gpg.d/devstructure.gpg http://packages.devstructure.com/keyring.gpg
sudo apt-get update
sudo apt-get -y install blueprint




#############################
# INSTALL SYSTEM DEPENDENCIES
#############################

sudo apt-get install --no-install-recommends apache2 libapache2-mod-wsgi \
libapache2-mod-python memcached python-dev python-cairo-dev \
python-django python-ldap python-memcache python-pysqlite2 \
sqlite3 erlang-os-mon erlang-snmp rabbitmq-server
    
sudo pip install django-tagging

mkdir /opt/graphite

sudo pip install carbon --install-option="--prefix=/opt/graphite" --install-option="--install-lib=/opt/graphite/lib"
sudo pip install graphite-web --install-option="--prefix=/opt/graphite" --install-option="--install-lib=/opt/graphite/webapp"
sudo pip install whisper

$ cd /opt/graphite/conf/
$ sudo cp carbon.conf.example carbon.conf
$ sudo cp storage-schemas.conf.example storage-schemas.conf


$ wget http://launchpad.net/graphite/0.9/0.9.9/+download/graphite-web-0.9.9.tar.gz
$ tar -zxvf graphite-web-0.9.9.tar.gz
$ mv graphite-web-0.9.9 graphite
$ cd graphite
$ sudo python check-dependencies.py
$ sudo python setup.py install

##################
# CONFIGURE APACHE
##################

$ cd graphite/examples
$ sudo cp example-graphite-vhost.conf /etc/apache2/sites-available/default
$ sudo cp /opt/graphite/conf/graphite.wsgi.example /opt/graphite/conf/graphite.wsgi
$ sudo mkdir /etc/httpd
$ sudo mkdir /etc/httpd/wsgi
cd /etc/apache2/sites-enabled/
ln -s ../sites-available/default-graphite .
$ sudo /etc/init.d/apache2 reload

#########################
# CREATE INITIAL DATABASE 
#########################

$ cd /opt/graphite/webapp/graphite/
$ sudo python manage.py syncdb
$ sudo chown -R www-data:www-data /opt/graphite/storage/
$ sudo /etc/init.d/apache2 restart
$ sudo cp local_settings.py.example local_settings.py

################################
# START CARBON (data aggregator)
################################

$ cd /opt/graphite/
$ sudo ./bin/carbon-cache.py start