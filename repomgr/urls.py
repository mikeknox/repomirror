
from django.conf.urls.defaults import *

import repolib.config

from django.http import HttpResponse

import ConfigParser
import os

def index ( request ) :

    response = HttpResponse()
    config = ConfigParser.RawConfigParser()
    if not config.read( [ "/etc/repomirror.conf" , os.path.expanduser("~/.repomirror") ] ) :
        response.write( "Server Error\n" )
        return response
    sections = config.sections()
    if config.has_section( "global" ) :
        sections.pop( sections.index( "global" ) )
    keylist =  ( 'type' , 'url' , 'version' , 'architectures' )
    response.write( "<table>\n" )
    response.write( "<thead>\n" )
    response.write( "<tr>\n" )
    response.write( "<th>Name</th>\n" )
    for key in keylist :
        response.write( "<th>%s</th>\n" % key )
    response.write( "</tr>\n" )
    response.write( "</thead>\n" )
    response.write( "<tbody>\n" )
    for section in sections :
        repo = repolib.config.__config( section , repolib.config.MirrorConf , config )
        if config.has_option ( section , "url" ) :
            repo['url'] = config.get( section , "url" )
        else :
            scheme = config.get( section , "scheme" )
            server = config.get( section , "server" )
            base_path = config.get( section , "base_path" )
            repo.set_url( scheme , server , base_path )
        response.write( "<tr>\n" )
        response.write( "<td><a href=%s>%s</a></td>\n" % ( section , repo.__name__ ) )
        for key in keylist :
            response.write( "<td>%s</td>\n" % repo[key] )
        response.write( "</tr>\n" )
    response.write( "</tbody>\n" )
    response.write( "</table>\n" )

    return response


def detail ( request , repo_name ) :

    response = HttpResponse()
    config = ConfigParser.RawConfigParser()
    if not config.read( [ "/etc/repomirror.conf" , os.path.expanduser("~/.repomirror") ] ) :
        response.write( "Server Error\n" )
        return response
    if not config.has_section( repo_name ) :
        response.write( "Repository '%s' does not exists\n" % repo_name )
        return response
    _global = []
    if config.has_section( "global" ) :
        _global = map( lambda x : "%s:%s" % x , config.items('global') )
    repo = map( lambda x : "%s:%s" % x , config.items(repo_name) )
    response.write( "<h3>%s</h3>\n" % repo_name )
    response.write( "<ul>\n" )
    for item in config.items( repo_name ) :
        response.write( "<li><b>%s</b> - %s\n" % item )
    response.write( "</ul>\n" )

    response.write( "<a href=./>Go to main page</a>\n" )

    return response


urlpatterns = patterns('',
    (r'^$', index),
    (r'^(?P<repo_name>.+)$', detail )
)
