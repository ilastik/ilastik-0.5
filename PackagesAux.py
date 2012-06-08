# -*- coding: utf-8 -*-

import __builtin__
import sys, urllib2, os, shutil, urlparse, re, subprocess, json, hashlib
import argparse, tarfile, inspect

import PackagesGlobals

if sys.version_info < (2, 7):
    print "Python version 2.7 or greater required."
    sys.exit(1)

def create_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)

#using http://www.pytips.com/2010/5/29/a-quick-md5sum-equivalent-in-python
#using http://stackoverflow.com/questions/22676/
#             how-do-i-download-a-file-over-http-using-python
def sha1sum(filename, buf_size = 0x80000):
    m = hashlib.sha1()
    # the with statement makes sure the file will be closed 
    with open(filename) as f:
        # We read the file in small chunk until EOF
        data = f.read(buf_size)
        while data:
            # We had data to the sha1 hash
            m.update(data)
            data = f.read(buf_size)
    # We return the sha1 hash in hexadecimal format
    return m.hexdigest()

# XXXXXXXXXXXXX check return values of os.system/etc...

def past_last_slash(x):
    return x.split('/')[-1]

def git_clone(url, directory):
    if not os.path.exists(directory):
        print "* cloning from git"
        os.system('git clone ' + url + ' ' + directory)

def git_pull(url, directory):
    print "* update from git"
    os.system('cd ' + directory + ' && git pull')

def git_clone_pull(url, directory):
    git_clone(url, directory)
    git_pull(url, directory)

def git_update(url, directory, tree_ish):
    git_clone(url, directory)
    # test if the commit named 'tree_ish' is missing from the local git repo:
    if subprocess.call('cd ' + directory + ' && git rev-parse --quiet --no-revs'
                       + ' --symbolic-full-name --verify '
                       + tree_ish, shell = True):
        git_pull(url, directory)

def git_archive(directory, tree_ish, output_file):
    # expressly disallow relative names.
    suffix = re.split('[\^\@\~]', past_last_slash(tree_ish))[0]
    branches = subprocess.check_output('cd ' + directory + ' && git branch',
                                       shell = True).splitlines()
    branches = [(name.strip(" *")) for name in branches]
    branches.append('HEAD')
    print(branches)
    if (suffix in branches):
        raise NameError("in an ilastik build, relative commit names ('" + suffix
                        + "') are disallowed for checkouts from git "
                        "repositories ('" + past_last_slash(directory) + "')")
    os.system('git archive -o ' + output_file + ' --remote='
              + directory + ' --prefix=' + directory + '/ ' + tree_ish)

# 3 things: a)  the JSON entry "archive": the canonical name of the build script
#           b)  the name of the downloaded file, usually versioned a la 'x.y.z'
#           c)  the sha1sum, to be added to the JSON data
# once a file is donloaded (b)), it is not supposed to be overwritten
# or downloaded once more

def download_file_from(url, download_file):
    print "Downloading file from", url
    try:
        r = urllib2.urlopen(urllib2.Request(url))
    except urllib2.HTTPError as e:
        print("Download from url '" + url + "' failed:")
        print(e)
        sys.exit(101)
    try:
        with open(download_file, 'wb') as f:
            shutil.copyfileobj(r, f)
    finally:
        r.close()

def sha1_failed(download_file, sha1_sum):
    return sha1_sum != None and sha1sum(download_file) != sha1_sum

def download_sha1_check(url, download_file, sha1_sum, sha1_log):
    download_file_from(url, download_file)
    if sha1_failed(download_file, sha1_sum):
        print ('sha1 mismatch of downloaded file \'%s\', aborting'
               % download_file)
        sys.exit(102)
    if sha1_log:
        print >>sha1_log, sha1_sum, download_file

def download(url, directory, sha1_sum = None, sha1_log = None):
    download_name = past_last_slash(url)
    create_dir(directory)
    download_file = directory + "/" + download_name
    if os.path.exists(download_file):
        print 'file \'%s\' already downloaded' % download_file
        # check sha1sum -- retry once if faulty (interrupted downloads, etc.)
        if sha1_failed(download_file, sha1_sum):
            print 'sha1 mismatch, re-downloading file once'
            download_sha1_check(url, download_file, sha1_sum, sha1_log)
    else:
        download_sha1_check(url, download_file, sha1_sum, sha1_log)
    return download_file

def json_get(file_name):
    try:
        with open(file_name) as file:
            return json.load(file)
    except ValueError as e:
        print("Invalid JSON syntax in file '" + file_name + "':")
        print(e)
        print("probably a stray ',': consider running\n\t"
              + "perl -pi -0777 -ne 's/(\s*,)+(\s*[\}\]])/\\2/g' "
              + file_name)
        sys.exit(107)

def json_put(data, file_name):
    with open(file_name, 'w') as out_json:
        json.dump(data, out_json, indent = 4)
        print >>out_json, ""

def tar_exclude_name(x):
    def name_filter(tarinfo):
        if tarinfo.name == x:
            return None
        else:
            return tarinfo
    return name_filter

def make_tar_files(tar_dir, repo_dir, repo_data, release_data, sha1_log,
                   release_file_name, release_default_name, script_dir):
    all_licenses_dir = 'licenses/'
    pkg_tar = tarfile.open(tar_dir + "ilastik_packages.tar", "w")
    old_dir = os.getcwd()
    os.chdir(repo_dir)
    for package in repo_data:
        directory = package["pkg"]
        print(directory)
        url = package["uri_all"]
        archive = package["archive"]
        if url.startswith("git://"):
            tag = release_data[directory] # tag from release control file
            git_update(url, directory, tag)
            print("Using git repository " + directory + ", commit "
                  + tag + ", for ilastik build:")
            archive_path = tar_dir + archive
            git_archive(directory, tag, archive_path)
        else:
            sha1_sum = package["sha1_all"]
            archive_path = download(url, directory, sha1_sum, sha1_log)
            ###package["sha1_all"] = sha1sum(archive_path)

        # tar file archive_path with name archive
        pkg_tar.add(archive_path, arcname = archive)

        license_uri = package["license_uri"]
        license_dir = all_licenses_dir + directory
        download(license_uri, license_dir)

    pkg_tar.add(all_licenses_dir)
    # add all build scripts
    os.chdir(script_dir)
    pkg_tar.add('.', filter = tar_exclude_name("./" + release_default_name))
    # add the actually used repo file
    os.chdir(old_dir)
    pkg_tar.add(release_file_name, arcname = release_default_name)
    pkg_tar.close()
    ##json_put(repo_data, 'out.json')

def cond_get(x, key):
    if key in x:
        return x[key]
    else:
        return None

def make_head_release(repo_dir, repo_data, release_file_name):
    release_data = json_get(release_file_name)
    old_dir = os.getcwd()
    os.chdir(repo_dir)
    for package in repo_data:
        directory = package["pkg"]
        url = package["uri_all"]
        if url.startswith("git://") and not cond_get(package, "external_repo"):
            git_clone_pull(url, directory)
            tag = subprocess.check_output('cd ' + directory
                                          + ' && git rev-parse HEAD',
                                          shell = True)
            release_data[directory] = tag.strip()

    os.chdir(old_dir)
    json_put(release_data, release_file_name)
    

def main():
    release_default_name = PackagesGlobals.release_default_name()

    cmd_line = argparse.ArgumentParser(description
                                       = "create ilastik sources tar file")
    cmd_line.add_argument('-m', '--make-head-release', action = "store_true",
                          help = "write remote HEAD git ids to release control "
                                 + "file ('release.json')")
    cmd_line.add_argument('-a', '--repositories', default =
                                '/export/home/users/mip/ilastik/build/repos',
                                help = "directory for the repository archives")
    cmd_line.add_argument('-r', '--release', default = release_default_name,
                                help = "release control file")
    cmd_line.add_argument('tar_file_directory', help = "output directory")
    args = cmd_line.parse_args()

    repo_dir = args.repositories
    release_file_name = args.release
    
    repo_data = json_get("repo-table.json")

    script_dir = os.path.dirname(os.path.abspath(inspect.getfile(
                                                 inspect.currentframe())))
    if args.make_head_release:
        print "writing HEAD git ids to file '" + release_file_name + "'"
        make_head_release(repo_dir, repo_data, release_file_name)
    else:
        release_data = json_get(release_file_name)
        with open(repo_dir + '/sha1.sums', 'a') as sha1_log:
            tar_dir = args.tar_file_directory + '/'
            make_tar_files(tar_dir, repo_dir, repo_data, release_data, sha1_log,
                           release_file_name, release_default_name, script_dir)


if __name__ == '__main__':
    main()
