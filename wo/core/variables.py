"""WordOps core variable module"""
import configparser
import os
from datetime import datetime
from re import match
from socket import getfqdn
from shutil import copy2

from distro import linux_distribution
from sh import git


class WOVar():
    """Intialization of core variables"""

    # WordOps version
    wo_version = "3.16.3"
    # WordOps packages versions
    wo_wp_cli = "2.4.0"
    wo_adminer = "4.7.5"
    wo_phpmyadmin = "5.0.2"
    wo_extplorer = "2.1.13"
    wo_dashboard = "1.2"

    # Get WPCLI path
    wo_wpcli_path = '/usr/local/bin/wp'

    # Current date and time of System
    wo_date = datetime.now().strftime('%d%b%Y-%H-%M-%S')

    # WordOps core variables
    # linux distribution
    wo_distro = linux_distribution(
        full_distribution_name=False)[0].lower()
    wo_platform_version = linux_distribution(
        full_distribution_name=False)[1].lower()
    # distro codename (bionic, xenial, stretch ...)
    wo_platform_codename = linux_distribution(
        full_distribution_name=False)[2].lower()

    # Get timezone of system
    if os.path.isfile('/etc/timezone'):
        with open("/etc/timezone", mode='r', encoding='utf-8') as tzfile:
            wo_timezone = tzfile.read().replace('\n', '')
            if wo_timezone == "Etc/UTC":
                wo_timezone = "UTC"
    else:
        wo_timezone = "Europe/Amsterdam"

    # Get FQDN of system
    wo_fqdn = getfqdn()

    # WordOps default webroot path
    wo_webroot = '/var/www/'

    # WordOps default renewal  SSL certificates path
    wo_ssl_archive = '/etc/letsencrypt/renewal'

    # WordOps default live SSL certificates path
    wo_ssl_live = '/etc/letsencrypt/live'

    # PHP user
    wo_php_user = 'www-data'

    # WordOps git configuration management
    config = configparser.ConfigParser()
    config.read(os.path.expanduser("~") + '/.gitconfig')
    try:
        wo_user = config['user']['name']
        wo_email = config['user']['email']
    except Exception:
        print("WordOps (wo) require an username & and an email "
              "address to configure Git (used to save server configurations)")
        print("Your informations will ONLY be stored locally")

        wo_user = input("Enter your name: ")
        while wo_user == "":
            print("Unfortunately, this can't be left blank")
            wo_user = input("Enter your name: ")

        wo_email = input("Enter your email: ")

        while not match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$",
                        wo_email):
            print("Whoops, seems like you made a typo - "
                  "the e-mail address is invalid...")
            wo_email = input("Enter your email: ")

        git.config("--global", "user.name", "{0}".format(wo_user))
        git.config("--global", "user.email", "{0}".format(wo_email))

    if not os.path.isfile('/root/.gitconfig'):
        copy2(os.path.expanduser("~") + '/.gitconfig', '/root/.gitconfig')

    # MySQL hostname
    wo_mysql_host = ""
    config = configparser.RawConfigParser()
    if os.path.exists('/etc/mysql/conf.d/my.cnf'):
        cnfpath = "/etc/mysql/conf.d/my.cnf"
    else:
        cnfpath = os.path.expanduser("~") + "/.my.cnf"
    if [cnfpath] == config.read(cnfpath):
        try:
            wo_mysql_host = config.get('client', 'host')
        except configparser.NoOptionError:
            wo_mysql_host = "localhost"
    else:
        wo_mysql_host = "localhost"

    # WordOps stack installation variables
    # Nginx repo and packages
    if wo_distro == 'ubuntu':
        wo_nginx_repo = "ppa:wordops/nginx-wo"
        wo_extra_repo = (
            "deb http://download.opensuse.org"
            "/repositories/home:/virtubox:"
            "/WordOps/xUbuntu_{0}/ /".format(wo_platform_version))
    else:
        if wo_distro == 'debian':
            if wo_platform_codename == 'jessie':
                wo_deb_repo = "Debian_8.0"
            elif wo_platform_codename == 'stretch':
                wo_deb_repo = "Debian_9.0"
            elif wo_platform_codename == 'buster':
                wo_deb_repo = "Debian_10"
        elif wo_distro == 'raspbian':
            if wo_platform_codename == 'stretch':
                wo_deb_repo = "Raspbian_9.0"
            elif wo_platform_codename == 'buster':
                wo_deb_repo = "Raspbian_10"
        # debian/raspbian nginx repository
        wo_nginx_repo = ("deb http://download.opensuse.org"
                         "/repositories/home:"
                         "/virtubox:/WordOps/{0}/ /"
                         .format(wo_deb_repo))

    wo_nginx = ["nginx-custom", "nginx-wo"]
    wo_nginx_key = '188C9FB063F0247A'

    wo_module = ["fpm", "curl", "gd", "imap",
                 "readline", "common",
                 "cli", "mbstring", "intl",
                 "bcmath", "mysql", "opcache",
                 "zip", "xml", "soap", "memcached",
                 "imagick", "igbinary", "msgpack",
                 "redis", "xdebug"]
    wo_php72 = []
    for module in wo_module:
        wo_php72 = wo_php72 + ["php7.2-{0}".format(module)]
    wo_php72 = wo_php72 + ["php7.2-recode"]
    wo_php73 = []
    for module in wo_module:
        wo_php73 = wo_php73 + ["php7.3-{0}".format(module)]
    wo_php73 = wo_php73 + ["php7.3-recode"]
    wo_php74 = []
    for module in wo_module:
        wo_php74 = wo_php74 + ["php7.4-{0}".format(module)]
    wo_php84 = []
    for module in wo_module:
        wo_php84 = wo_php84 + ["php8.4-{0}".format(module)]

    wo_php_extra = ["graphviz"]

    wo_mysql = [
        "mariadb-server", "percona-toolkit",
        "mariadb-common", "python3-mysqldb"]
    if wo_distro == 'raspbian':
        if wo_platform_codename == 'stretch':
            mariadb_ver = '10.1'
        else:
            mariadb_ver = '10.3'
    else:
        mariadb_ver = '10.5'
        wo_mysql = wo_mysql + ["mariadb-backup"]

    wo_mysql_client = ["mariadb-client", "python3-mysqldb"]

    wo_fail2ban = ["fail2ban"]
    wo_clamav = ["clamav", "clamav-freshclam"]
    wo_ubuntu_backports = 'ppa:jonathonf/backports'

    # APT repositories
    wo_mysql_repo = ("deb [arch=amd64,arm64,ppc64el] "
                     "http://mariadb.mirrors.ovh.net/MariaDB/repo/"
                     "10.5/{distro} {codename} main"
                     .format(distro=wo_distro,
                             codename=wo_platform_codename))
    if wo_distro == 'ubuntu':
        wo_php_repo = "ppa:ondrej/php"
        wo_redis_repo = ("ppa:redislabs/redis")
        wo_goaccess_repo = ("ppa:alex-p/goaccess")

    else:
        wo_php_repo = (
            "deb https://packages.sury.org/php/ {codename} main"
            .format(codename=wo_platform_codename))
        wo_php_key = 'AC0E47584A7A714D'
        wo_redis_repo = ("deb https://packages.sury.org/php/ {codename} all"
                         .format(codename=wo_platform_codename))

    wo_redis = ['redis-server']

    # Repo path
    wo_repo_file = "wo-repo.list"
    wo_repo_file_path = ("/etc/apt/sources.list.d/" + wo_repo_file)

    # Application dabase file path
    basedir = os.path.abspath(os.path.dirname('/var/lib/wo/'))
    wo_db_uri = 'sqlite:///' + os.path.join(basedir, 'dbase.db')

    def __init__(self):
        pass
