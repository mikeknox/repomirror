
import os

import urllib2

import repoutils


def instantiate_repo ( config , mirror_mode=True ) :
    repo = None
    if mirror_mode :
        if config['type'] == "yum" :
            repo = yum_repository( config )
        elif config['type'] == "centos" :
            repo = centos_repository( config )
        elif config['type'] == "yum_upd" :
            repo = fedora_update_repository( config )
        elif config['type'] == "centos_upd" :
            repo = centos_update_repository( config )
        elif config['type'] == "deb" :
            repo = debian_repository( config )
        elif config['type'] == "yast2" :
            repo = yast2_repository( config )
        elif config['type'] == "yast2_update" :
            repo = yast2_update_repository( config )
        else :
            repoutils.show_error( "Unknown repository type '%s'" % config['type'] )
    else :
        if config['type'] == "deb" :
            repo = debian_build_repository( config )
        else :
            repoutils.show_error( "Unknown repository build type '%s'" % config['type'] )
    return repo


class _repository :

    def __init__ ( self , config ) :

	self.destdir = config[ "destdir" ]
        self.version = config[ "version" ]

        self.architectures = config[ "architectures" ]

        if not os.path.isdir( self.destdir ) :
            raise Exception( "Destination directory %s does not exists" % self.destdir )


class abstract_repository ( _repository ) :

    def __init__ ( self , config ) :
	_repository.__init__( self , config )
        self.repo_url = urllib2.urlparse.urljoin( "%s/" % config[ "url" ] , "" )
        self.params = config[ "params" ]

    def base_url ( self ) :
        raise Exception( "Calling an abstract method" )

    def repo_path ( self ) :
        raise Exception( "Calling an abstract method" )

    def metadata_path ( self , subrepo=None , partial=False ) :
        raise Exception( "Calling an abstract method" )

    def get_signed_metafile ( self , params , meta_file , sign_ext=".asc" ) :

        local_file = os.path.join( self.repo_path() , meta_file )

        if params['usegpg'] :

            signature_file = self._retrieve_file( urllib2.urlparse.urljoin( self.base_url() , meta_file + sign_ext ) )

            if not signature_file :
                repoutils.show_error( "Signature file for version '%s' not found." % ( self.version ) )
                return

            if os.path.isfile( local_file ) :
                errstr = repoutils.gpg_error( signature_file , local_file )
                if errstr :
                    repoutils.show_error( errstr , False )
                    os.unlink( local_file )
                else :
                    os.unlink( signature_file )
                    # FIXME : If we consider that our mirror is complete, it is safe to exit here
                    if params['mode'] == "update" :
                        repoutils.show_error( "Metadata file unchanged, exiting" , False )
                        return True
                    return local_file

        else :
            if os.path.isfile( local_file ) :
                os.unlink( local_file )

        # FIXME : produce error if we reach this point with existing local_file
        if not os.path.isfile( local_file ) :

            release_file = self._retrieve_file( urllib2.urlparse.urljoin( self.base_url() , meta_file ) )

            if not release_file :
                repoutils.show_error( "Release file for suite '%s' is not found." % ( self.version ) )
                if params['usegpg'] :
                    os.unlink( signature_file )
                return

            if params['usegpg'] :
                errstr = repoutils.gpg_error( signature_file , release_file )
                os.unlink( signature_file )
                if errstr :
                    repoutils.show_error( errstr )
                    os.unlink( release_file )
                    return

        return release_file

    def build_local_tree( self ) :

        suite_path = self.repo_path()

        for subrepo in self.get_subrepos() :
            packages_path = self.metadata_path( subrepo , False )
            if not os.path.exists( os.path.join( suite_path , packages_path ) ) :
                os.makedirs( os.path.join( suite_path , packages_path ) )

    def _retrieve_file ( self , location , localname=None ) :

        try :
            filename  = repoutils.downloadRawFile( location , localname )
        except urllib2.URLError , ex :
            repoutils.show_error( "Exception : %s" % ex )
            return
        except urllib2.HTTPError , ex :
            repoutils.show_error( "Exception : %s" % ex )
            return

        return filename


class abstract_build_repository ( _repository ) :

    def __init__ ( self , config ) :
	_repository.__init__( self , config )


from yum import *

from debian import *
