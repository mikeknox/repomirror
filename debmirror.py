#!/usr/bin/python

# FIXME : Allow reading from a sources.list file, parsing into scheme, server, path, codename and components

scheme = "http"
server = "ftp.es.debian.org"
base_path = "debian"
destdir = "/home/jpalacios/repomirror"
destdir = "/shares/internal/PUBLIC/mirrors"

codename = "lenny"
architectures = [ "i386" , "amd64" ]
components = [ "main" , "contrib" ]
#
sections = []
priorities = []
tags = []

# FIXME : Create a separate program to list all the sections, pririties and tags

import debian_bundle.deb822 , debian_bundle.debian_support

import md5

import urllib2

import os , sys
import tempfile

extensions = {}

try :
    import gzip
    extensions['.gz'] = gzip.open
except :
    pass
    
try :
    import bz2
    extensions['.bz2'] = bz2.BZ2File
except :
    pass


def downloadRawFile ( remote , local=None ) :
    """Downloads a remote file to the local system.

    remote - URL
    local - Optional local name for the file

    Returns the local file name"""

    if not local :
        (handle, fname) = tempfile.mkstemp()
    else :
        fname = local
        handle = os.open( fname , os.O_WRONLY | os.O_TRUNC | os.O_CREAT )
    try:
        response = urllib2.urlopen( remote )
        data = response.read(256)
        while data :
            os.write(handle, data)
            data = response.read(256)
        os.close(handle)
    except Exception ,ex :
        print "Exception : %s" % ex
        os.close(handle)
        if not local :
            os.unlink(fname)
        return None
    return fname

def md5_error ( filename , item , bsize=128 ) :
    if os.stat( filename ).st_size != int( item['size'] ) :
        return "Bad file size '%s'" % filename
    if calc_md5( filename , bsize ) != item['md5sum'] :
        return "Bad MD5 checksum '%s'" % filename
    return None

def calc_md5(filename, bsize=128):
    f = open( filename , 'rb' )
    _md5 = md5.md5()
    data = f.read(bsize)
    while data :
        _md5.update(data)
        data = f.read(bsize)
    f.close()
    return _md5.hexdigest()

def gpg_error( signature , file , full_verification=False ) :

    if full_verification :
        return _gpg_error( signature , file )

    # FIXME : Use a temporary file instead of a fixed name one
    signature_file = "/tmp/signa"
    fd = open( signature )
    sigfd = open( signature_file , 'w' )
    line = fd.readline()
    while line :
        sigfd.write( line )
        if line[:-1] == "-----END PGP SIGNATURE-----" :
            sigfd.close()
            if not _gpg_error( signature_file , file ) :
                fd.close()
                return False
            sigfd = open( signature_file , 'w' )
        line = fd.readline()
    else :
        sigfd.close()
    fd.close()
    return "All signatures failed"

def _gpg_error( signature , file ) :
    gpgerror = "Not verified"
    try :
        result = GnuPGInterface.GnuPG().run( [ "--verify", signature , file ] )
        result.wait()
        gpgerror = False
    except IOError , ex :
        gpgerror = "Bad signatute : %s" % ex
    return gpgerror

def show_error( str , error=True ) :
    if error :
        print "ERROR : %s" % str
    else :
        print "WARNING : %s" % str


# This gets built to the typical path on source.list
repo_url = "%s://%s/%s" % ( scheme , server , base_path )

base_url = "%s/dists/%s" % ( repo_url , codename )

suite_path = os.path.join( destdir , codename )

pool_path = os.path.join( destdir , "pool" )

local_release = os.path.join( suite_path , "Release" )


#WD#try :
#WD#    release_pgp_file = downloadRawFile( "%s/Release.gpg" % base_url )
#WD#except urllib2.URLError , ex :
#WD#    print "Exception : %s" % ex
#WD#    sys.exit(255)
#WD#except urllib2.HTTPError , ex :
#WD#    print "Exception : %s" % ex
#WD#    sys.exit(255)
#WD#
#WD#if not release_pgp_file :
#WD#    show_error( "Release.gpg file for suite '%s' is not found." % ( codename ) )
#WD#    sys.exit(255)

if os.path.isfile( local_release ) :
#WD#    errstr = gpg_error( release_pgp_file , local_release )
#WD#    if errstr :
#WD#        show_error( errstr , False )
#WD#        os.unlink( local_release )
#WD#    else :
#WD#        # FIXME : If we consider that our mirror is complete, it is safe to exit here
        release = debian_bundle.deb822.Release( sequence=open( local_release ) )
#WD#        os.unlink( release_pgp_file )


if not os.path.isfile( local_release ) :

    try :
        release_file = downloadRawFile( "%s/Release" % base_url )
    except urllib2.URLError , ex :
        print "Exception : %s" % ex
        sys.exit(255)
    except urllib2.HTTPError , ex :
        print "Exception : %s" % ex
        sys.exit(255)

    if not release_file :
        show_error( "Release file for suite '%s' is not found." % ( codename ) )
        os.unlink( release_pgp_file )
        sys.exit(255)

#WD#    errstr = gpg_error( release_pgp_file , release_file )
#WD#    os.unlink( release_pgp_file )
#WD#    if errstr :
#WD#        show_error( errstr )
#WD#        os.unlink( release_file )
#WD#        sys.exit(255)

    release = debian_bundle.deb822.Release( sequence=open( release_file ) )
    
    
# FIXME : Why not check also against release['Codename'] ??
if release['Suite'].lower() == codename.lower() :
    show_error( "You have supplied suite '%s'. Please use codename '%s' instead" % ( codename, release['Codename'] ) )
    os.unlink( release_file )
    sys.exit(1)

release_comps = release['Components'].split()
for comp in components :
    if comp not in release_comps :
        show_error( "Component '%s' is not available ( %s )" % ( comp , " ".join(release_comps) ) )
        sys.exit(1)

release_archs = release['Architectures'].split()
for arch in architectures :
    if arch not in release_archs :
        show_error( "Architecture '%s' is not available ( %s )" % ( arch , " ".join(release_archs) ) )
        sys.exit(1)

# After verify all the mirroring parameters, it is safe to create directory tree

if not os.path.exists( suite_path ) :
    os.mkdir( suite_path )

if not os.path.exists( local_release ) :
    os.rename( release_file , local_release )

for comp in components :
    if not os.path.exists( os.path.join( suite_path , comp ) ) :
        os.mkdir( os.path.join( suite_path , comp ) )
    for arch in architectures :
        packages_path = os.path.join( comp , "binary-%s" % arch )
        if not os.path.exists( os.path.join( suite_path , packages_path ) ) :
            os.mkdir( os.path.join( suite_path , packages_path ) )

if not os.path.exists( pool_path ) :
    os.mkdir( pool_path )

for comp in components :
    pool_com_path = os.path.join( pool_path , comp )
    if not os.path.exists( pool_com_path ) :
        os.mkdir( pool_com_path )

print """
Mirroring %(Label)s %(Version)s (%(Codename)s)
%(Origin)s %(Suite)s , %(Date)s
""" % release
print "Components : %s\nArchitectures : %s\n" % ( " ".join(components) , " ".join(architectures) )


download_pkgs = {}
download_size = 0

release_sections = []
release_priorities = []
release_tags = []

for comp in components :

    for arch in architectures :

        print "Scanning %s / %s" % ( comp , arch )

        # Downloading Release file is quite redundant

        localname = None
        read_handler = None

        for ( extension , read_handler ) in extensions.iteritems() :

            localname = os.path.join( suite_path , "%s/Packages%s" % ( packages_path , extension ) )

            if os.path.isfile( localname ) :
                #
                # IMPROVEMENT : For Release at least, and _multivalued in general : Multivalued fields returned as dicts instead of lists
                #
                # FIXME : 'size' element should be a number !!!
                #
                # FIXME : What about other checksums (sha1, sha256)
                for item in release['MD5Sum'] :
                    if item['name'] == "%s/Packages%s" % ( packages_path , extension ) :
                        error = md5_error( localname , item )
                        if error :
                            show_error( error , False )
                            os.unlink( localname )
                        break
                else :
                    show_error( "Checksum for file '%s/Packages%s' not found, go to next format." % ( packages_path , extension ) , True )
                    continue

                if os.path.isfile( localname ) :
                    # FIXME : If we consider that our mirror is complete, we should break one more loop, for the next component-architecture pair
                    show_error( "Local copy of '%s/Packages%s' is up-to-date." % ( packages_path , extension ) , False )
                    break
        else :

            show_error( "No local Packages file exist for %s / %s. Downloading." % ( comp , arch ) , True )

            for ( extension , read_handler ) in extensions.iteritems() :

                localname = os.path.join( suite_path , "%s/Packages%s" % ( packages_path , extension ) )
                url = "%s/%s/Packages%s" % ( base_url , packages_path , extension )

                if downloadRawFile( url , localname ) :
                    #
                    # IMPROVEMENT : For Release at least, and _multivalued in general : Multivalued fields returned as dicts instead of lists
                    #
                    # FIXME : 'size' element should be a number !!!
                    #
                    # FIXME : What about other checksums (sha1, sha256)
                    for item in release['MD5Sum'] :
                        if item['name'] == "%s/Packages%s" % ( packages_path , extension ) :
                            error = md5_error( localname , item )
                            if error :
                                show_error( error , False )
                                os.unlink( localname )
                                sys.exit(2)
                            break
                    else :
                        show_error( "Checksum for file '%s' not found, exiting." % item['name'] ) 
                        sys.exit(0)

                    break

            else :
                show_error( "No Valid Packages file found for %s / %s" % ( comp , arch ) )
                sys.exit(0)


        # NOTE : The block below will usually be only useful when a new Packages is downloaded, but we
        #        run through it every time to account for changes in minor filters (sections, priorities, ... )

        fd = read_handler( localname )
        packages = debian_bundle.debian_support.PackageFile( localname , fileObj=fd )

# FIXME : If any minor filter is used, Packages file must be recreated for the exported repo
#         Solution : Disable filtering on first approach
#         In any case, the real problem is actually checksumming, reconstructiog Release and signing

        print "Scanning available packages for minor filters"
        for pkg in packages :
            pkginfo = debian_bundle.deb822.Deb822Dict( pkg )

            # NOTE : Is this actually a good idea ?? It simplifies, but I would like to mirror main/games but not contrib/games, for example
            # SOLUTION : Create a second and separate Category with the last part (filename) of Section
            # For now, we kept the simplest way
            if pkginfo['Section'].find("%s/"%comp) == 0 :
                pkginfo['Section'] = pkginfo['Section'][pkginfo['Section'].find("/")+1:]

            if pkginfo['Section'] not in release_sections :
                release_sections.append( pkginfo['Section'] )
            if pkginfo['Priority'] not in release_priorities :
                release_priorities.append( pkginfo['Priority'] )
            if 'Tag' in pkginfo.keys() and pkginfo['Tag'] not in release_tags :
                release_tags.append( pkginfo['Tag'] )

            if sections and pkginfo['Section'] not in sections :
                continue
            if priorities and pkginfo['Priority'] not in priorities :
                continue
            if tags and 'Tag' in pkginfo.keys() and pkginfo['Tag'] not in tags :
                continue

            pkg_key = "%s-%s" % ( pkginfo['Package'] , pkginfo['Architecture'] )
            if pkg_key in download_pkgs.keys() :
                if pkginfo['Architecture'] != "all" :
                    show_error( "Package '%s - %s' is duplicated in repositories" % ( pkginfo['Package'] , pkginfo['Architecture'] ) , False )
            else :
                download_pkgs[ pkg_key ] = pkginfo
                # FIXME : This might cause a ValueError exception ??
                download_size += int( pkginfo['Size'] )

        print "Current download size : %.1f Mb" % ( download_size / 1024 / 1024 )
        fd.close()


# print "All sects",release_sections
# print "All prios",release_priorities
# # print "All tags",release_tags


_size = download_size / 1024 / 1024
if _size > 2048 :
    print "Total size to download : %.1f Gb" % ( _size / 1024 )
else :
    print "Total size to download : %.1f Mb" % ( _size )

for pkg in download_pkgs.values() :

    destname = os.path.join( destdir , pkg['Filename'] )

    # FIXME : Perform this check while appending to download_pkgs ???
    if os.path.isfile( destname ) :
        error = md5_error( destname , pkg )
        if error :
            show_error( error , False )
            os.unlink( destname )
        else :
            continue
    else :
        path , name = os.path.split( destname )
        if not os.path.exists( path ) :
            os.makedirs( path )

    if not downloadRawFile ( "%s/%s" % ( repo_url , pkg['Filename'] ) , destname ) :
        show_error( "Failure downloading file '%s'" % ( pkg['Filename'] ) , False )
