"""Logfile Plugin for WordOps"""

import glob
import gzip
import os

from cement.core.controller import CementBaseController, expose

from wo.cli.plugins.site_functions import logwatch
from wo.core.fileutils import WOFileUtils
from wo.core.logging import Log
from wo.core.mysql import WOMysql
from wo.core.sendmail import WOSendMail
from wo.core.shellexec import WOShellExec
from wo.core.variables import WOVar


def wo_log_hook(app):
    pass


class WOLogController(CementBaseController):
    class Meta:
        label = 'log'
        description = 'Perform operations on Nginx, PHP and MySQL log files'
        stacked_on = 'base'
        stacked_type = 'nested'
        usage = "wo log [<site_name>] [options]"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()


class WOLogShowController(CementBaseController):
    class Meta:
        label = 'show'
        description = 'Show Nginx, PHP, MySQL log file'
        stacked_on = 'log'
        stacked_type = 'nested'
        arguments = [
            (['--all'],
                dict(help='Show All logs file', action='store_true')),
            (['--nginx'],
                dict(help='Show Nginx Error logs file', action='store_true')),
            (['--php'],
                dict(help='Show PHP Error logs file', action='store_true')),
            (['--fpm'],
                dict(help='Show PHP-FPM slow logs file',
                     action='store_true')),
            (['--mysql'],
                dict(help='Show MySQL logs file', action='store_true')),
            (['--wp'],
                dict(help='Show Site specific WordPress logs file',
                     action='store_true')),
            (['--access'],
                dict(help='Show Nginx access log file',
                     action='store_true')),
            (['site_name'],
                dict(help='Website Name', nargs='?', default=None))
        ]
        usage = "wo log show [<site_name>] [options]"

    @expose(hide=True)
    def default(self):
        """Default function of log show"""
        self.msg = []

        if self.app.pargs.php:
            self.app.pargs.nginx = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (not self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.fpm = True
            self.app.pargs.mysql = True
            self.app.pargs.access = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.wp = True
            self.app.pargs.access = True
            self.app.pargs.mysql = True

        if self.app.pargs.nginx and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*error.log"]

        if self.app.pargs.access and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*access.log"]

        if self.app.pargs.fpm:
            open('/var/log/php/7.2/slow.log', 'a').close()
            open('/var/log/php7.2-fpm.log', 'a').close()
            self.msg = self.msg + ['/var/log/php/7.2/slow.log',
                                   '/var/log/php7.2-fpm.log']
        if self.app.pargs.mysql:
            # MySQL debug will not work for remote MySQL
            if WOVar.wo_mysql_host == "localhost":
                if os.path.isfile('/var/log/mysql/mysql-slow.log'):
                    self.msg = self.msg + ['/var/log/mysql/mysql-slow.log']
                else:
                    Log.info(self, "MySQL slow-log not found, skipped")
            else:
                Log.warn(self, "Remote MySQL found, WordOps does not support"
                         "remote MySQL servers or log files")

        if self.app.pargs.site_name:
            webroot = "{0}{1}".format(WOVar.wo_webroot,
                                      self.app.pargs.site_name)

            if not os.path.isdir(webroot):
                Log.error(self, "Site not present, quitting")
            if self.app.pargs.access:
                self.msg = self.msg + ["{0}/{1}/logs/access.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.nginx:
                self.msg = self.msg + ["{0}/{1}/logs/error.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.wp:
                if os.path.isdir('{0}/htdocs/web/app'.format(webroot)):
                    if not os.path.isfile('{0}/logs/debug.log'
                                          .format(webroot)):
                        if not os.path.isfile('{0}/htdocs/web/app/debug.log'
                                              .format(webroot)):
                            open("{0}/htdocs/web/app/debug.log"
                                 .format(webroot),
                                 encoding='utf-8', mode='a').close()
                            WOShellExec.cmd_exec(self, "chown {1}: {0}/htdocs/"
                                                 "web/app/debug.log"
                                                 "".format(webroot,
                                                           WOVar
                                                           .wo_php_user)
                                                 )
                    # create symbolic link for debug log
                    WOFileUtils.create_symlink(self, ["{0}/htdocs/web/app/"
                                                      "debug.log"
                                                      .format(webroot),
                                                      '{0}/logs/debug.log'
                                                      .format(webroot)])

                    self.msg = self.msg + ["{0}/{1}/logs/debug.log"
                                           .format(WOVar.wo_webroot,
                                                   self.app.pargs.site_name)]
                else:
                    Log.info(self, "Site is not WordPress site, skipping "
                             "WordPress logs")

        watch_list = []
        for w_list in self.msg:
            watch_list = watch_list + glob.glob(w_list)

        logwatch(self, watch_list)


class WOLogResetController(CementBaseController):
    class Meta:
        label = 'reset'
        description = 'Reset Nginx, PHP, MySQL log file'
        stacked_on = 'log'
        stacked_type = 'nested'
        arguments = [
            (['--all'],
                dict(help='Reset All logs file', action='store_true')),
            (['--nginx'],
                dict(help='Reset Nginx Error logs file', action='store_true')),
            (['--php'],
                dict(help='Reset PHP Error logs file', action='store_true')),
            (['--fpm'],
                dict(help='Reset PHP-FPM slow logs file',
                     action='store_true')),
            (['--mysql'],
                dict(help='Reset MySQL logs file', action='store_true')),
            (['--wp'],
                dict(help='Reset Site specific WordPress logs file',
                     action='store_true')),
            (['--access'],
                dict(help='Reset Nginx access log file',
                     action='store_true')),
            (['--slow-log-db'],
                dict(help='Drop all rows from slowlog table in database',
                     action='store_true')),
            (['site_name'],
                dict(help='Website Name', nargs='?', default=None))
        ]
        usage = "wo log reset [<site_name>] [options]"

    @expose(hide=True)
    def default(self):
        """Default function of log reset"""
        self.msg = []

        if self.app.pargs.php:
            self.app.pargs.nginx = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
            (not self.app.pargs.wp) and (not self.app.pargs.site_name) and
                (not self.app.pargs.slow_log_db)):
            self.app.pargs.nginx = True
            self.app.pargs.fpm = True
            self.app.pargs.mysql = True
            self.app.pargs.access = True
            self.app.pargs.slow_log_db = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
            (not self.app.pargs.wp) and (self.app.pargs.site_name) and
                (not self.app.pargs.slow_log_db)):
            self.app.pargs.nginx = True
            self.app.pargs.wp = True
            self.app.pargs.access = True
            self.app.pargs.mysql = True

        if self.app.pargs.slow_log_db:
            if os.path.isdir("/var/www/22222/htdocs/db/anemometer"):
                Log.info(self, "Resetting MySQL slow_query_log database table")
                WOMysql.execute(self, "TRUNCATE TABLE  "
                                "slow_query_log.global_query_review_history")
                WOMysql.execute(self, "TRUNCATE TABLE "
                                "slow_query_log.global_query_review")

        if self.app.pargs.nginx and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*error.log"]

        if self.app.pargs.access and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*access.log"]

        if self.app.pargs.fpm:
            open('/var/log/php/7.2/slow.log', 'a').close()
            open('/var/log/php7.2-fpm.log', 'a').close()
            self.msg = self.msg + ['/var/log/php/7.2/slow.log',
                                   '/var/log/php7.2-fpm.log']
        if self.app.pargs.mysql:
            # MySQL debug will not work for remote MySQL
            if WOVar.wo_mysql_host == "localhost":
                if os.path.isfile('/var/log/mysql/mysql-slow.log'):
                    self.msg = self.msg + ['/var/log/mysql/mysql-slow.log']
                else:
                    Log.info(self, "MySQL slow-log not found, skipped")
            else:
                Log.warn(self, "Remote MySQL found, WordOps does not support"
                         "remote MySQL servers or log files")

        if self.app.pargs.site_name:
            webroot = "{0}{1}".format(WOVar.wo_webroot,
                                      self.app.pargs.site_name)

            if not os.path.isdir(webroot):
                Log.error(self, "Site not present, quitting")
            if self.app.pargs.access:
                self.msg = self.msg + ["{0}/{1}/logs/access.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.nginx:
                self.msg = self.msg + ["{0}/{1}/logs/error.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.wp:
                if os.path.isdir('{0}/htdocs/web/app'.format(webroot)):
                    if not os.path.isfile('{0}/logs/debug.log'
                                          .format(webroot)):
                        if not os.path.isfile('{0}/htdocs/web/app/debug.log'
                                              .format(webroot)):
                            open("{0}/htdocs/web/app/debug.log"
                                 .format(webroot),
                                 encoding='utf-8', mode='a').close()
                            WOShellExec.cmd_exec(self, "chown {1}: {0}/htdocs/"
                                                 "web/app/debug.log"
                                                 "".format(webroot,
                                                           WOVar
                                                           .wo_php_user)
                                                 )
                    # create symbolic link for debug log
                    WOFileUtils.create_symlink(self, ["{0}/htdocs/web/app/"
                                                      "debug.log"
                                                      .format(webroot),
                                                      '{0}/logs/debug.log'
                                                      .format(webroot)])

                    self.msg = self.msg + ["{0}/{1}/logs/debug.log"
                                           .format(WOVar.wo_webroot,
                                                   self.app.pargs.site_name)]
                else:
                    Log.info(self, "Site is not WordPress site, skipping "
                             "WordPress logs")

        reset_list = []
        for r_list in self.msg:
            reset_list = reset_list + glob.glob(r_list)

        # Clearing content of file
        for r_list in reset_list:
            Log.info(self, "Resetting file {file}".format(file=r_list))
            open(r_list, 'w').close()


class WOLogGzipController(CementBaseController):
    class Meta:
        label = 'gzip'
        description = 'GZip Nginx, PHP, MySQL log file'
        stacked_on = 'log'
        stacked_type = 'nested'
        arguments = [
            (['--all'],
                dict(help='GZip All logs file', action='store_true')),
            (['--nginx'],
                dict(help='GZip Nginx Error logs file', action='store_true')),
            (['--php'],
                dict(help='GZip PHP Error logs file', action='store_true')),
            (['--fpm'],
                dict(help='GZip PHP-FPM slow logs file',
                     action='store_true')),
            (['--mysql'],
                dict(help='GZip MySQL logs file', action='store_true')),
            (['--wp'],
                dict(help='GZip Site specific WordPress logs file',
                     action='store_true')),
            (['--access'],
                dict(help='GZip Nginx access log file',
                     action='store_true')),
            (['site_name'],
                dict(help='Website Name', nargs='?', default=None))
        ]
        usage = "wo log gzip [<site_name>] [options]"

    @expose(hide=True)
    def default(self):
        """Default function of log GZip"""
        self.msg = []

        if self.app.pargs.php:
            self.app.pargs.nginx = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (not self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.fpm = True
            self.app.pargs.mysql = True
            self.app.pargs.access = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.wp = True
            self.app.pargs.access = True
            self.app.pargs.mysql = True

        if self.app.pargs.nginx and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*error.log"]

        if self.app.pargs.access and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*access.log"]

        if self.app.pargs.fpm:
            open('/var/log/php/7.2/slow.log', 'a').close()
            open('/var/log/php7.2-fpm.log', 'a').close()
            self.msg = self.msg + ['/var/log/php/7.2/slow.log',
                                   '/var/log/php7.2-fpm.log']
        if self.app.pargs.mysql:
            # MySQL debug will not work for remote MySQL
            if WOVar.wo_mysql_host == "localhost":
                if os.path.isfile('/var/log/mysql/mysql-slow.log'):
                    self.msg = self.msg + ['/var/log/mysql/mysql-slow.log']
                else:
                    Log.info(self, "MySQL slow-log not found, skipped")

            else:
                Log.warn(self, "Remote MySQL found, WordOps does not support"
                         "remote MySQL servers or log files")

        if self.app.pargs.site_name:
            webroot = "{0}{1}".format(WOVar.wo_webroot,
                                      self.app.pargs.site_name)

            if not os.path.isdir(webroot):
                Log.error(self, "Site not present, quitting")
            if self.app.pargs.access:
                self.msg = self.msg + ["{0}/{1}/logs/access.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.nginx:
                self.msg = self.msg + ["{0}/{1}/logs/error.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.wp:
                if os.path.isdir('{0}/htdocs/web/app'.format(webroot)):
                    if not os.path.isfile('{0}/logs/debug.log'
                                          .format(webroot)):
                        if not os.path.isfile('{0}/htdocs/web/app/debug.log'
                                              .format(webroot)):
                            open("{0}/htdocs/web/app/debug.log"
                                 .format(webroot),
                                 encoding='utf-8', mode='a').close()
                            WOShellExec.cmd_exec(self, "chown {1}: {0}/htdocs/"
                                                 "web/app/debug.log"
                                                 "".format(webroot,
                                                           WOVar
                                                           .wo_php_user)
                                                 )
                    # create symbolic link for debug log
                    WOFileUtils.create_symlink(self, ["{0}/htdocs/web/app/"
                                                      "debug.log"
                                                      .format(webroot),
                                                      '{0}/logs/debug.log'
                                                      .format(webroot)])

                    self.msg = self.msg + ["{0}/{1}/logs/debug.log"
                                           .format(WOVar.wo_webroot,
                                                   self.app.pargs.site_name)]
                else:
                    Log.info(self, "Site is not WordPress site, skipping "
                             "WordPress logs")

        gzip_list = []
        for g_list in self.msg:
            gzip_list = gzip_list + glob.glob(g_list)

        # Gzip content of file
        for g_list in gzip_list:
            Log.info(self, "Gzipping file {file}".format(file=g_list))
            in_file = g_list
            in_data = open(in_file, "rb").read()
            out_gz = g_list + ".gz"
            gzf = gzip.open(out_gz, "wb")
            gzf.write(in_data)
            gzf.close()


class WOLogMailController(CementBaseController):
    class Meta:
        label = 'mail'
        description = 'Mail Nginx, PHP, MySQL log file'
        stacked_on = 'log'
        stacked_type = 'nested'
        arguments = [
            (['--all'],
                dict(help='Mail All logs file', action='store_true')),
            (['--nginx'],
                dict(help='Mail Nginx Error logs file', action='store_true')),
            (['--php'],
                dict(help='Mail PHP 7.2 Error logs file',
                     action='store_true')),
            (['--fpm'],
                dict(help='Mail PHP 7.2-fpm slow logs file',
                     action='store_true')),
            (['--mysql'],
                dict(help='Mail MySQL logs file', action='store_true')),
            (['--wp'],
                dict(help='Mail Site specific WordPress logs file',
                     action='store_true')),
            (['--access'],
                dict(help='Mail Nginx access log file',
                     action='store_true')),
            (['site_name'],
                dict(help='Website Name', nargs='?', default=None)),
            (['--to'],
             dict(help='Email addresses to send log files', action='append',
                  dest='to', nargs=1, required=True)),
        ]
        usage = "wo log mail [<site_name>] [options]"

    @expose(hide=True)
    def default(self):
        """Default function of log Mail"""
        self.msg = []

        if self.app.pargs.php:
            self.app.pargs.nginx = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (not self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.fpm = True
            self.app.pargs.mysql = True
            self.app.pargs.access = True

        if ((not self.app.pargs.nginx) and (not self.app.pargs.fpm) and
            (not self.app.pargs.mysql) and (not self.app.pargs.access) and
                (not self.app.pargs.wp) and (self.app.pargs.site_name)):
            self.app.pargs.nginx = True
            self.app.pargs.wp = True
            self.app.pargs.access = True
            self.app.pargs.mysql = True

        if self.app.pargs.nginx and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*error.log"]

        if self.app.pargs.access and (not self.app.pargs.site_name):
            self.msg = self.msg + ["/var/log/nginx/*access.log"]

        if self.app.pargs.fpm:
            open('/var/log/php/7.2/slow.log', 'a').close()
            open('/var/log/php7.2-fpm.log', 'a').close()
            self.msg = self.msg + ['/var/log/php/7.2/slow.log',
                                   '/var/log/php7.2-fpm.log']
        if self.app.pargs.mysql:
            # MySQL debug will not work for remote MySQL
            if WOVar.wo_mysql_host == "localhost":
                if os.path.isfile('/var/log/mysql/mysql-slow.log'):
                    self.msg = self.msg + ['/var/log/mysql/mysql-slow.log']
                else:
                    Log.info(self, "MySQL slow-log not found, skipped")
            else:
                Log.warn(self, "Remote MySQL found, WordOps does not support"
                         "remote MySQL servers or log files")

        if self.app.pargs.site_name:
            webroot = "{0}{1}".format(WOVar.wo_webroot,
                                      self.app.pargs.site_name)

            if not os.path.isdir(webroot):
                Log.error(self, "Site not present, quitting")
            if self.app.pargs.access:
                self.msg = self.msg + ["{0}/{1}/logs/access.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.nginx:
                self.msg = self.msg + ["{0}/{1}/logs/error.log"
                                       .format(WOVar.wo_webroot,
                                               self.app.pargs.site_name)]
            if self.app.pargs.wp:
                if os.path.isdir('{0}/htdocs/web/app'.format(webroot)):
                    if not os.path.isfile('{0}/logs/debug.log'
                                          .format(webroot)):
                        if not os.path.isfile('{0}/htdocs/web/app/debug.log'
                                              .format(webroot)):
                            open("{0}/htdocs/web/app/debug.log"
                                 .format(webroot),
                                 encoding='utf-8', mode='a').close()
                            WOShellExec.cmd_exec(self, "chown {1}: {0}/htdocs/"
                                                 "web/app/debug.log"
                                                 "".format(webroot,
                                                           WOVar
                                                           .wo_php_user)
                                                 )
                    # create symbolic link for debug log
                    WOFileUtils.create_symlink(self, ["{0}/htdocs/web/app/"
                                                      "debug.log"
                                                      .format(webroot),
                                                      '{0}/logs/debug.log'
                                                      .format(webroot)])

                    self.msg = self.msg + ["{0}/{1}/logs/debug.log"
                                           .format(WOVar.wo_webroot,
                                                   self.app.pargs.site_name)]
                else:
                    Log.info(self, "Site is not WordPress site, skipping "
                             "WordPress logs")

        mail_list = []
        for m_list in self.msg:
            mail_list = mail_list + glob.glob(m_list)

        for tomail in self.app.pargs.to:
            Log.info(self, "Sending mail to {0}".format(tomail[0]))
            WOSendMail("wordops", tomail[0], "{0} Log Files"
                       .format(WOVar.wo_fqdn),
                       "Hi,\n  The requested logfiles are attached."
                       "\n\nBest regards,\nYour WordOps worker",
                       files=mail_list, port=25, isTls=False)


def load(app):
    # register the plugin class.. this only happens if the plugin is enabled
    app.handler.register(WOLogController)
    app.handler.register(WOLogShowController)
    app.handler.register(WOLogResetController)
    app.handler.register(WOLogGzipController)
    app.handler.register(WOLogMailController)
    # register a hook (function) to run after arguments are parsed.
    app.hook.register('post_argument_parsing', wo_log_hook)
